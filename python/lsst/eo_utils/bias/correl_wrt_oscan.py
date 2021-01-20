"""Tasks to analyze the correlation between the overscan and the imaging region"""

import numpy as np

from lsst.eo_utils.base.defaults import getSlotList

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_dims_from_ccd,\
    get_raw_image, get_geom_regions, get_amp_list, get_image_frames_2d

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .analysis import BiasAnalysisConfig, BiasAnalysisTask

from .meta_analysis import BiasRaftTableAnalysisConfig, BiasRaftTableAnalysisTask,\
    BiasSummaryAnalysisConfig, BiasSummaryAnalysisTask



class CorrelWRTOscanConfig(BiasAnalysisConfig):
    """Configuration for CorrelWRTOscanTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='biasoscorr')


class CorrelWRTOscanTask(BiasAnalysisTask):
    """Analyze correlations between the imaging section
    and the overscan regions in a series of bias frames"""

    ConfigClass = CorrelWRTOscanConfig
    _DefaultName = "CorrelWRTOscanTask"
    iteratorClass = AnalysisBySlot

    clip_value = 50.

    plot_names = ['row', 'col']

    def extract(self, butler, data, **kwargs):
        """Extract the correlations between the imaging section
        and the overscan regions in a series of bias frames

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

        self.log_info_slot_msg(self.config, "%i files" % len(bias_files))

        ref_frames = {}

        nfiles = len(bias_files)
        s_correl = np.ndarray((16, nfiles-1))
        p_correl = np.ndarray((16, nfiles-1))

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            ccd = self.get_ccd(butler, bias_file, mask_files)
            if ifile == 0:
                dims = get_dims_from_ccd(ccd)
                nrow_i = dims['nrow_i']
                ncol_i = dims['ncol_i']
                amps = get_amp_list(ccd)
                for i, amp in enumerate(amps):
                    regions = get_geom_regions(ccd, amp)
                    image = get_raw_image(ccd, amp)
                    ref_frames[i] = get_image_frames_2d(image, regions)
                    continue
            self.get_ccd_data(ccd, ref_frames,
                              ifile=ifile, s_correl=s_correl, p_correl=p_correl,
                              nrow_i=nrow_i, ncol_i=ncol_i)

        self.log_progress("Done!")

        data = {}
        for i in range(16):
            data['s_correl_a%02i' % i] = s_correl[i]
            data['p_correl_a%02i' % i] = p_correl[i]

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        dtables.make_datatable("correl", data)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the correlations between the imaging section
        and the overscan regions

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
        figs.setup_amp_plots_grid("row",
                                  title="Correlation: imaging region and serial overscan",
                                  xlabel="Correlation",
                                  ylabel="Number of frames")
        figs.setup_amp_plots_grid("col",
                                  title="Correlation: imaging region and paralell overscan",
                                  xlabel="Correlation",
                                  ylabel="Number of frames")

        dtab = dtables.get_table("correl")
        for i in range(16):
            s_correl = dtab['s_correl_a%02i' % i]
            p_correl = dtab['p_correl_a%02i' % i]
            figs.get_obj('row', 'axs').flat[i].hist(s_correl, bins=100, range=(-1., 1.))
            figs.get_obj('col', 'axs').flat[i].hist(p_correl, bins=100, range=(-1., 1.))


    def get_ccd_data(self, ccd, ref_frames, **kwargs):
        """Get the bias values and update the data dictionary

        Parameters
        ----------
        ccd : `MaskedCCD`
            The ccd we are getting data from
        data : `dict`
            The data we are updating

        Keywords
        --------
        ifile : `int`
            The file index
        s_correl : `array`
            Serial overscan correlations
        p_correl : `array`
            Parallel overscan correlations
        """
        ifile = kwargs['ifile']
        s_correl = kwargs['s_correl']
        p_correl = kwargs['p_correl']
        nrow_i = kwargs['nrow_i']
        ncol_i = kwargs['ncol_i']

        amps = get_amp_list(ccd)
        for i, amp in enumerate(amps):

            regions = get_geom_regions(ccd, amp)
            image = get_raw_image(ccd, amp)
            frames = get_image_frames_2d(image, regions)

            del_i_array = frames['imaging'] - ref_frames[i]['imaging']
            del_s_array = frames['serial_overscan'] - ref_frames[i]['serial_overscan']
            del_p_array = frames['parallel_overscan'] - ref_frames[i]['parallel_overscan']

            dd_s = del_s_array.mean(1)[0:nrow_i]-del_i_array.mean(1)
            dd_p = del_p_array.mean(0)[0:ncol_i]-del_i_array.mean(0)
            mask_s = np.fabs(dd_s) < self.clip_value
            mask_p = np.fabs(dd_p) < self.clip_value

            s_correl[i, ifile-1] = np.corrcoef(del_s_array.mean(1)[0:nrow_i][mask_s],
                                               dd_s[mask_s])[0, 1]
            p_correl[i, ifile-1] = np.corrcoef(del_p_array.mean(0)[0:ncol_i][mask_p],
                                               dd_p[mask_p])[0, 1]


class CorrelWRTOscanStatsConfig(BiasRaftTableAnalysisConfig):
    """Configuration for CorrelWRTOscanStatsTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='biasoscorr')
    filekey = EOUtilOptions.clone_param('filekey', default='biasoscorr-stats')

class CorrelWRTOscanStatsTask(BiasRaftTableAnalysisTask):
    """Extract statistics about the correlation between
    the overscan and imaging regions in bias frames"""

    ConfigClass = CorrelWRTOscanStatsConfig
    _DefaultName = "CorrelWRTOscanStatsTask"

    plot_names = ['mean-s', 'mean-p']

    def extract(self, butler, data, **kwargs):
        """Extract the the summary statistics data

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
            self.log.warn("Ignoring butler.")

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


        self.log_info_raft_msg(self.config, "")

        slot_list = self.config.slots
        if slot_list is None:
            slot_list = getSlotList(self.config.raft)

        for islot, slot in enumerate(slot_list):

            self.log_progress("  %s" % slot)
            basename = data[slot]
            datapath = basename.replace('biasoscorr_stats.fits', 'biasoscorr.fits')

            try:
                dtables = TableDict(datapath, [datakey])
                table = dtables[datakey]
            except FileNotFoundError:
                self.log.error("Could not open %s\n" % datapath)
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

        self.log_progress("Done!")

        outtables = TableDict()
        outtables.make_datatable("biasoscorr_stats", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the statistics study

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
        sumtable = dtables['biasoscorr_stats']
        figs.plot_stat_color('mean-s', sumtable['s_correl_mean'].reshape(9, 16))
        figs.plot_stat_color('mean-p', sumtable['p_correl_mean'].reshape(9, 16))



class CorrelWRTOscanSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOscanSummaryTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='biasoscorr-stats')
    filekey = EOUtilOptions.clone_param('filekey', default='biasoscorr-sum')


class CorrelWRTOscanSummaryTask(BiasSummaryAnalysisTask):
    """Summarize the results for the analysis correlation between imaging
    and overscan regions"""

    ConfigClass = CorrelWRTOscanSummaryConfig
    _DefaultName = "CorrelWRTOscanSummaryTask"

    plot_names = ['mean-s', 'mean-p']

    def extract(self, butler, data, **kwargs):
        """Make a summry table

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
            data[key] = val.replace('biasoscorr_sum.fits', 'biasoscorr_stats.fits')

        if not self.config.skip:
            outtable = vstack_tables(data, tablename='biasoscorr_stats')

        dtables = TableDict()
        dtables.add_datatable('biasoscorr_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data

        It should use a `TableDict` object to create a set of
        plots and fill a `FigureDict` object

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

        sumtable = dtables['biasoscorr_sum']
        runtable = dtables['runs']

        yvals_s = sumtable['s_correl_mean'].flatten().clip(0., 1.)
        yvals_p = sumtable['p_correl_mean'].flatten().clip(0., 1.)
        runs = runtable['runs']

        figs.plot_run_chart("mean-s", runs, yvals_s,
                            ylabel="Correlation between serial overscan and imaging")
        figs.plot_run_chart("mean-p", runs, yvals_p,
                            ylabel="Correlation between parallel overscan and imaging")


EO_TASK_FACTORY.add_task_class('CorrelWRTOscan', CorrelWRTOscanTask)
EO_TASK_FACTORY.add_task_class('CorrelWRTOscanStats', CorrelWRTOscanStatsTask)
EO_TASK_FACTORY.add_task_class('CorrelWRTOscanSummary', CorrelWRTOscanSummaryTask)
