"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_dims_from_ccd, get_ccd_from_id,\
    get_raw_image, get_geom_regions, get_amp_list, get_image_frames_2d

from .file_utils import raft_bias_tablename, raft_bias_plotname,\
    bias_summary_tablename, bias_summary_plotname

from .analysis import BiasAnalysisConfig, BiasAnalysisTask, BiasAnalysisBySlot

from .meta_analysis import BiasSummaryByRaft, BiasTableAnalysisByRaft,\
    BiasSummaryAnalysisConfig, BiasSummaryAnalysisTask



class CorrelWRTOScanConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='biasoscorr')
    bias = EOUtilConfig.clone_param('bias')
    mask = EOUtilConfig.clone_param('mask')


class CorrelWRTOScanTask(BiasAnalysisTask):
    """Class to analyze correlations between the imaging section
    and the overscan regions in a series of bias frames"""

    ConfigClass = CorrelWRTOScanConfig
    _DefaultName = "CorrelWRTOScanTask"
    iteratorClass = BiasAnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor"""
        BiasAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract the correlations between the imaging section
        and the overscan regions in a series of bias frames

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs:
            slot (str)           Slot in question, i.e., 'S00'

        @returns (`TableDict`) with the extracted data
        """
        self.safe_update(**kwargs)
        slot = self.config.slot

        bias_files = data['BIAS']
        mask_files = get_mask_files(**kwargs)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        ref_frames = {}

        nfiles = len(bias_files)
        s_correl = np.ndarray((16, nfiles-1))
        p_correl = np.ndarray((16, nfiles-1))

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)
            if ifile == 0:
                dims = get_dims_from_ccd(butler, ccd)
                nrow_i = dims['nrow_i']
                ncol_i = dims['ncol_i']
                amps = get_amp_list(butler, ccd)
                for i, amp in enumerate(amps):
                    regions = get_geom_regions(butler, ccd, amp)
                    image = get_raw_image(butler, ccd, amp)
                    ref_frames[i] = get_image_frames_2d(image, regions)
                    continue
            self.get_ccd_data(butler, ccd, ref_frames,
                              ifile=ifile, s_correl=s_correl, p_correl=p_correl,
                              nrow_i=nrow_i, ncol_i=ncol_i)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        data = {}
        for i in range(16):
            data['s_correl_a%02i' % i] = s_correl[i]
            data['p_correl_a%02i' % i] = p_correl[i]

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        dtables.make_datatable("correl", data)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the bias structure

        @param dtables (`TableDict`)  The data
        @param figs (`FigureDict`)    Object to store the figues
        """
        self.safe_update(**kwargs)
        figs.setup_amp_plots_grid("oscorr-row", title="Correlation: imaging region and serial overscan",
                                  xlabel="Correlation",
                                  ylabel="Number of frames")
        figs.setup_amp_plots_grid("oscorr-col", title="Correlation: imaging region and paralell overscan",
                                  xlabel="Correlation",
                                  ylabel="Number of frames")

        df = dtables.get_table("correl")
        for i in range(16):
            s_correl = df['s_correl_a%02i' % i]
            p_correl = df['p_correl_a%02i' % i]
            figs.get_obj('oscorr-row', 'axs').flat[i].hist(s_correl, bins=100, range=(-1., 1.))
            figs.get_obj('oscorr-col', 'axs').flat[i].hist(p_correl, bins=100, range=(-1., 1.))


    @staticmethod
    def get_ccd_data(butler, ccd, ref_frames, **kwargs):
        """Get the bias values and update the data dictionary

        @param butler (`Butler`)   The data butler
        @param ccd (`MaskedCCD`)   The ccd we are getting data from
        @param ref_frames (dict)   Reference data
        @param kwargs:
          ifile (int)                 The file index
          s_correl (np.array)         Serial overscan correlations
          p_correl (np.array)         Parallel overscan correlations
        """
        ifile = kwargs['ifile']
        s_correl = kwargs['s_correl']
        p_correl = kwargs['p_correl']
        nrow_i = kwargs['nrow_i']
        ncol_i = kwargs['ncol_i']

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):

            regions = get_geom_regions(butler, ccd, amp)
            image = get_raw_image(butler, ccd, amp)
            frames = get_image_frames_2d(image, regions)

            ref_i_array = ref_frames[i]['imaging']
            ref_s_array = ref_frames[i]['serial_overscan']
            ref_p_array = ref_frames[i]['parallel_overscan']

            del_i_array = frames['imaging'] - ref_i_array
            del_s_array = frames['serial_overscan'] - ref_s_array
            del_p_array = frames['parallel_overscan'] - ref_p_array

            dd_s = del_s_array.mean(1)[0:nrow_i]-del_i_array.mean(1)
            dd_p = del_p_array.mean(0)[0:ncol_i]-del_i_array.mean(0)
            mask_s = np.fabs(dd_s) < 50.
            mask_p = np.fabs(dd_p) < 50.

            s_correl[i, ifile-1] = np.corrcoef(del_s_array.mean(1)[0:nrow_i][mask_s],
                                               dd_s[mask_s])[0, 1]
            p_correl[i, ifile-1] = np.corrcoef(del_p_array.mean(0)[0:ncol_i][mask_p],
                                               dd_p[mask_p])[0, 1]


class CorrelWRTOScanStatsConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='_biasoscorr')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')


class CorrelWRTOScanStatsTask(BiasAnalysisTask):
    """Class to analyze the overscan correlation with imaging region"""

    ConfigClass = CorrelWRTOScanStatsConfig
    _DefaultName = "CorrelWRTOScanStatsTask"
    iteratorClass = BiasTableAnalysisByRaft
    tablefile_name = raft_bias_tablename
    plotfile_name = raft_bias_plotname

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
            sys.stdout.write("Ignoring butler in bias_fft_stats.extract\n")

        datakey = 'correl'

        data_dict = dict(s_correl_mean=[],
                         s_correl_median=[],
                         s_correl_std=[],
                         s_correl_min=[],
                         s_correl_max=[],
                         p_correl_mean=[],
                         p_correl_median=[],
                         p_correl_std=[],
                         p_correl_min=[],
                         p_correl_max=[],
                         slot=[],
                         amp=[])

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace('.fits', 'biasoscorr.fits')

            try:
                dtables = TableDict(datapath, [datakey])
                table = dtables[datakey]
            except FileNotFoundError:
                sys.stderr.write("Warning, could not open %s\n" % datapath)
                table = None

            for amp in range(16):
                if table is not None:
                    tablevals_s = table['s_correl_a%02i' % amp]
                    tablevals_p = table['p_correl_a%02i' % amp]
                    mask_s = np.isfinite(tablevals_s)
                    mask_p = np.isfinite(tablevals_p)
                    if mask_s.sum() > 0:
                        tablevals_s = tablevals_s[mask_s]
                    else:
                        tablevals_s = [0., 0.]
                    if mask_p.sum() > 0:
                        tablevals_p = tablevals_p[mask_p]
                    else:
                        tablevals_p = [0., 0.]
                else:
                    tablevals_s = [0., 0.]
                    tablevals_p = [0., 0.]
                data_dict['s_correl_mean'].append(np.mean(tablevals_s))
                data_dict['s_correl_median'].append(np.median(tablevals_s))
                data_dict['s_correl_std'].append(np.std(tablevals_s))
                data_dict['s_correl_min'].append(np.min(tablevals_s))
                data_dict['s_correl_max'].append(np.max(tablevals_s))
                data_dict['p_correl_mean'].append(np.mean(tablevals_p))
                data_dict['p_correl_median'].append(np.median(tablevals_p))
                data_dict['p_correl_std'].append(np.std(tablevals_p))
                data_dict['p_correl_min'].append(np.min(tablevals_p))
                data_dict['p_correl_max'].append(np.max(tablevals_p))
                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("biasoscorr_stats", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the bias fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)
        sumtable = dtables['biasoscorr_stats']
        figs.plot_stat_color('mean_oscorr_s', sumtable['s_correl_mean'].reshape(9, 16))
        figs.plot_stat_color('mean_oscorr_p', sumtable['p_correl_mean'].reshape(9, 16))



class CorrelWRTOScanSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='_biasoscorr_sum')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')


class CorrelWRTOScanSummaryTask(BiasSummaryAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = CorrelWRTOScanSummaryConfig
    _DefaultName = "CorrelWRTOScanSummaryTask"
    iteratorClass = BiasSummaryByRaft
    tablefile_name = bias_summary_tablename
    plotfile_name = bias_summary_plotname

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
            data[key] = val.replace('.fits', 'biasoscorr_stats.fits')

        if not kwargs.get('skip', False):
            outtable = vstack_tables(data, tablename='biasoscorr_stats')

        dtables = TableDict()
        dtables.add_datatable('biasoscorr_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the superbias statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)

        sumtable = dtables['biasoscorr_sum']
        runtable = dtables['runs']

        yvals_s = sumtable['s_correl_mean'].flatten().clip(0., 1.)
        yvals_p = sumtable['p_correl_mean'].flatten().clip(0., 1.)
        runs = runtable['runs']

        figs.plot_run_chart("s_correl_mean", runs, yvals_s, ylabel="Correlation between serial overscan and imaging")
        figs.plot_run_chart("p_correl_mean", runs, yvals_p, ylabel="Correlation between parallel overscan and imaging")
