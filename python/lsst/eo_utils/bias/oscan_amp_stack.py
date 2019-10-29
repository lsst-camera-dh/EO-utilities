"""Task to look for coherent noise by stacking the overscan from all the amplifiers"""

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions


from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import  REGION_KEYS,\
    get_dimension_arrays_from_ccd

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .data_utils import stack_by_amps, convert_stack_arrays_to_dict

from .analysis import BiasAnalysisConfig, BiasAnalysisTask

from .meta_analysis import BiasRaftTableAnalysisConfig, BiasRaftTableAnalysisTask,\
    BiasSummaryAnalysisConfig, BiasSummaryAnalysisTask



class OscanAmpStackConfig(BiasAnalysisConfig):
    """Configuration for OscanAmpStackTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasosstack')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class OscanAmpStackTask(BiasAnalysisTask):
    """Look for coherent noise by stacking the overscan from all the amplifiers"""

    ConfigClass = OscanAmpStackConfig
    _DefaultName = "OscanAmpStackTask"
    iteratorClass = AnalysisBySlot

    def extract(self, butler, data, **kwargs):
        """Stack the overscan region from all the amps on a sensor
        to look for coherent read noise

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        self.safe_update(**kwargs)

        bias_files = data['BIAS']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files=mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(bias_files))

        stack_arrays = {}

        nfiles = len(bias_files)

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            ccd = self.get_ccd(butler, bias_file, mask_files)

            if ifile == 0:
                dim_array_dict = get_dimension_arrays_from_ccd(ccd)
                for key, val in dim_array_dict.items():
                    stack_arrays[key] = np.zeros((nfiles, 16, len(val)))

            stack_by_amps(stack_arrays, ccd,
                          ifile=ifile, bias_type=self.config.bias,
                          superbias_frame=superbias_frame)

        self.log_progress("Done!")

        stackdata_dict = convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles)

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key, val in stackdata_dict.items():
            dtables.make_datatable('stack-%s' % key, val)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the stacked overscan region data

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)

        stats = ['mean', 'std', 'signif']
        stats_labels = ['Mean [ADU]', 'Std [ADU]', 'Significance [sigma]']
        for skey, slabel in zip(stats, stats_labels):
            y_name = "stack_%s" % skey
            figkey = "biasosstack-%s" % skey
            figs.setup_region_plots_grid(figkey, title="Amplifier Stacked Overscan Data",
                                         xlabel="Channel", ylabel=slabel)

            idx = 0
            for rkey in REGION_KEYS:
                for dkey in ['row', 'col']:
                    xkey = "%s_%s" % (dkey, rkey)
                    datakey = "stack-%s" % xkey
                    figs.plot_xy_axs_from_tabledict(dtables, datakey, idx, figkey,
                                                    x_name=xkey, y_name=y_name,
                                                    ymin=-10., ymax=10.)
                    idx += 1


class OscanAmpStackStatsConfig(BiasRaftTableAnalysisConfig):
    """Configuration for OscanAmpStackStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='biasosstack')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasosstack_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class OscanAmpStackStatsTask(BiasRaftTableAnalysisTask):
    """Extract statistics from overscan amplifier stacking analysis"""

    ConfigClass = OscanAmpStackStatsConfig
    _DefaultName = "OscanAmpStackStatsTask"

    def extract(self, butler, data, **kwargs):
        """Extract the summary statistics about the fluctuations

        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        self.safe_update(**kwargs)

        if butler is not None:
            self.log.warn("Ignoring bulter")

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

        self.log_info_raft_msg(self.config, "")

        for islot, slot in enumerate(ALL_SLOTS):

            self.log_progress("  %s" % slot)

            basename = data[slot]
            datapath = basename.replace('_stats.fits', '.fits')

            try:
                dtables = TableDict(datapath, ['stack-row_s', 'stack-col_p'])
                table_s = dtables['stack-row_s']
                table_p = dtables['stack-col_p']
            except FileNotFoundError:
                self.log.error("Could not open %s\n" % datapath)
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

        self.log_progress("Done!")

        outtables = TableDict()
        outtables.make_datatable("biasosstack_stats", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary statistics

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)
        #sumtable = dtables['biasosstack_stats']
        if dtables is not None:
            self.log.warning("No plots defined for OscanAmpStackStatsTask")


class OscanAmpStackSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='biasosstack_stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasosstack_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class OscanAmpStackSummaryTask(BiasSummaryAnalysisTask):
    """Summarize the results for the analysis of the overscan amplifeir stacking"""

    ConfigClass = OscanAmpStackSummaryConfig
    _DefaultName = "OscanAmpStackSummaryTask"

    def extract(self, butler, data, **kwargs):
        """Make a summary table

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        self.safe_update(**kwargs)

        if butler is not None:
            self.log.warn("Ignoring butler")

        for key, val in data.items():
            data[key] = val.replace('_sum.fits', '_stats.fits')

        outtable = vstack_tables(data, tablename='biasosstack_stats')

        dtables = TableDict()
        dtables.add_datatable('biasosstack_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
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
