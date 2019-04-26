"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import  REGION_KEYS,\
    get_ccd_from_id, get_dimension_arrays_from_ccd

from lsst.eo_utils.base.analysis import EO_TASK_FACTORY

from .file_utils import get_superbias_frame,\
    RAFT_BIAS_TABLE_FORMATTER, RAFT_BIAS_PLOT_FORMATTER

from .data_utils import stack_by_amps, convert_stack_arrays_to_dict

from .analysis import BiasAnalysisConfig, BiasAnalysisTask, BiasAnalysisBySlot

from .meta_analysis import BiasSummaryByRaft, BiasTableAnalysisByRaft,\
    BiasSummaryAnalysisConfig, BiasSummaryAnalysisTask



class OscanAmpStackConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    suffix = EOUtilOptions.clone_param('suffix', default='biasosstack')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class OscanAmpStackTask(BiasAnalysisTask):
    """Class to analyze correlations between the imaging section
    and the overscan regions in a series of bias frames"""

    ConfigClass = OscanAmpStackConfig
    _DefaultName = "OscanAmpStackTask"
    iteratorClass = BiasAnalysisBySlot

    def __init__(self, **kwargs):
        """ C'tor """
        BiasAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Stack the overscan region from all the amps on a sensor
        to look for coherent read noise

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the bias and mask files
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            bias (str)           Method to use for unbiasing
            superbias (str)      Method to use for superbias subtraction
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        bias_files = data['BIAS']
        mask_files = get_mask_files(self, **kwargs)
        superbias_frame = get_superbias_frame(self, mask_files=mask_files, **kwargs)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        stack_arrays = {}

        nfiles = len(bias_files)

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)

            if ifile == 0:
                dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)
                for key, val in dim_array_dict.items():
                    stack_arrays[key] = np.zeros((nfiles, 16, len(val)))

            stack_by_amps(stack_arrays, butler, ccd,
                          ifile=ifile, bias_type=self.config.bias,
                          superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        stackdata_dict = convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles)

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key, val in stackdata_dict.items():
            dtables.make_datatable('stack-%s' % key, val)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the bias structure

        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
        """
        self.safe_update(**kwargs)

        stats = ['mean', 'std', 'signif']
        stats_labels = ['Mean [ADU]', 'Std [ADU]', 'Significance [sigma]']
        for skey, slabel in zip(stats, stats_labels):
            y_name = "stack_%s" % skey
            figkey = "biasosstack-%s" % skey
            figs.setup_region_plots_grid(figkey, title=stats,
                                         xlabel="Channel", ylabel=slabel)

            idx = 0
            for rkey in REGION_KEYS:
                for dkey in ['row', 'col']:
                    xkey = "%s_%s" % (dkey, rkey)
                    datakey = "stack-%s" % xkey
                    figs.plot_xy_axs_from_tabledict(dtables, datakey, idx, figkey,
                                                    x_name=xkey, y_name=y_name)
                    idx += 1


class OscanAmpStackStatsConfig(BiasAnalysisConfig):
    """Configuration for OscanAmpStackStatsTask"""
    suffix = EOUtilOptions.clone_param('suffix', default='biasosstack_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class OscanAmpStackStatsTask(BiasAnalysisTask):
    """Class to analyze the overscan correlation with imaging region"""

    ConfigClass = OscanAmpStackStatsConfig
    _DefaultName = "OscanAmpStackStatsTask"
    iteratorClass = BiasTableAnalysisByRaft

    tablename_format = RAFT_BIAS_TABLE_FORMATTER
    plotname_format = RAFT_BIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor """
        BiasAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract the bias as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        if butler is not None:
            sys.stdout.write("Ignoring butler in OscanAmpStackStatsTask.extract\n")

        data_dict = dict(s_row_min_mean=[],
                         s_row_min_median=[],
                         s_row_min_std=[],
                         s_row_min_min=[],
                         s_row_min_max=[],
                         s_row_max_mean=[],
                         s_row_max_median=[],
                         s_row_max_std=[],
                         s_row_max_min=[],
                         s_row_max_max=[],
                         p_col_min_mean=[],
                         p_col_min_median=[],
                         p_col_min_std=[],
                         p_col_min_min=[],
                         p_col_min_max=[],
                         p_col_max_mean=[],
                         p_col_max_median=[],
                         p_col_max_std=[],
                         p_col_max_min=[],
                         p_col_max_max=[],
                         slot=[])

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace('_stats.fits', '.fits')

            try:
                dtables = TableDict(datapath, ['stack-row_s', 'stack-col_p'])
                table_s = dtables['stack-row_s']
                table_p = dtables['stack-col_p']
            except FileNotFoundError:
                sys.stderr.write("Warning, could not open %s\n" % datapath)
                table_s = None
                table_p = None

            if table_s is not None:
                tablevals_s_min = table_s['stack_mean'].min(0)
                tablevals_s_max = table_s['stack_mean'].max(0)
            else:
                tablevals_s_min = [0., 0.]
                tablevals_s_max = [0., 0.]

            if table_p is not None:
                tablevals_p_min = table_p['stack_mean'].min(0)
                tablevals_p_max = table_p['stack_mean'].max(0)
            else:
                tablevals_p_min = [0., 0.]
                tablevals_p_max = [0., 0.]

            data_dict['s_row_min_mean'].append(np.mean(tablevals_s_min))
            data_dict['s_row_min_median'].append(np.median(tablevals_s_min))
            data_dict['s_row_min_std'].append(np.std(tablevals_s_min))
            data_dict['s_row_min_min'].append(np.min(tablevals_s_min))
            data_dict['s_row_min_max'].append(np.max(tablevals_s_min))
            data_dict['s_row_max_mean'].append(np.mean(tablevals_s_max))
            data_dict['s_row_max_median'].append(np.median(tablevals_s_max))
            data_dict['s_row_max_std'].append(np.std(tablevals_s_max))
            data_dict['s_row_max_min'].append(np.min(tablevals_s_max))
            data_dict['s_row_max_max'].append(np.max(tablevals_s_max))
            data_dict['p_col_min_mean'].append(np.mean(tablevals_p_min))
            data_dict['p_col_min_median'].append(np.median(tablevals_p_min))
            data_dict['p_col_min_std'].append(np.std(tablevals_p_min))
            data_dict['p_col_min_min'].append(np.min(tablevals_p_min))
            data_dict['p_col_min_max'].append(np.max(tablevals_p_min))
            data_dict['p_col_max_mean'].append(np.mean(tablevals_p_max))
            data_dict['p_col_max_median'].append(np.median(tablevals_p_max))
            data_dict['p_col_max_std'].append(np.std(tablevals_p_max))
            data_dict['p_col_max_min'].append(np.min(tablevals_p_max))
            data_dict['p_col_max_max'].append(np.max(tablevals_p_max))
            data_dict['slot'].append(islot)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("biasosstack_stats", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the bias fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)
        sumtable = dtables['biasosstack_stats']


class OscanAmpStackSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    suffix = EOUtilOptions.clone_param('suffix', default='biasosstack_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class OscanAmpStackSummaryTask(BiasSummaryAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = OscanAmpStackSummaryConfig
    _DefaultName = "OscanAmpStackSummaryTask"
    iteratorClass = BiasSummaryByRaft

    def __init__(self, **kwargs):
        """C'tor"""
        BiasSummaryAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Make a summry table of the bias FFT data

        @param filedict (dict)      The files we are analyzing
        @param kwargs
            bias (str)
            superbias (str)

        @returns (TableDict)
        """
        self.safe_update(**kwargs)

        if butler is not None:
            sys.stdout.write("Ignoring butler in correl_wrt_oscan_summary.extract\n")

        for key, val in data.items():
            data[key] = val.replace('_sum.fits', '_stats.fits')

        outtable = vstack_tables(data, tablename='biasosstack_stats')

        dtables = TableDict()
        dtables.add_datatable('biasosstack_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the superbias statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)

        sumtable = dtables['biasosstack_sum']
        runtable = dtables['runs']

        yvals_s_min_mean = sumtable['s_row_min_mean']
        yvals_s_min_std = sumtable['s_row_min_std']
        yvals_s_max_mean = sumtable['s_row_max_mean']
        yvals_s_max_std = sumtable['s_row_max_std']
        yvals_p_min_mean = sumtable['p_col_min_mean']
        yvals_p_min_std = sumtable['p_col_min_std']
        yvals_p_max_mean = sumtable['p_col_max_mean']
        yvals_p_max_std = sumtable['p_col_max_std']

        runs = runtable['runs']

        yvals_s_diff = (yvals_s_max_mean - yvals_s_min_mean).clip(0, 100)
        yvals_s_err = np.sqrt(yvals_s_min_std**2 + yvals_s_max_std**2).clip(0, 10)
        yvals_p_diff = (yvals_p_max_mean - yvals_p_min_mean).clip(0, 100)
        yvals_p_err = np.sqrt(yvals_p_min_std**2 + yvals_p_max_std**2).clip(0, 10)

        figs.plot_run_chart("s_row_diff", runs, yvals_s_diff,
                            yerrs=yvals_s_err, ylabel="Amplitude of Row-wise amp stack [ADU]")
        figs.plot_run_chart("p_col_diff", runs, yvals_p_diff,
                            yerrs=yvals_p_err, ylabel="Amplitude of Col-wise amp stack [ADU]")


EO_TASK_FACTORY.add_task_class('OscanAmpStack', OscanAmpStackTask)
EO_TASK_FACTORY.add_task_class('OscanAmpStackStats', OscanAmpStackStatsTask)
EO_TASK_FACTORY.add_task_class('OscanAmpStackSummary', OscanAmpStackSummaryTask)
