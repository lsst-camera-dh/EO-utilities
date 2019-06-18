"""Class to analyze the correlations between the overscans for all amplifiers on a raft"""

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.stat_utils import gauss_fit

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    get_exposure_time, get_amp_list, get_raw_image, get_geom_regions

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .file_utils import SUPERDARK_FORMATTER

from .meta_analysis import DarkRaftTableAnalysisConfig,\
    DarkRaftTableAnalysisTask,\
    DarkSummaryAnalysisConfig, DarkSummaryAnalysisTask


class DarkCurrentConfig(DarkRaftTableAnalysisConfig):
    """Configuration for DarkCurrentTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    insuffix = EOUtilOptions.clone_param('insuffix', default='')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='dark_current')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class DarkCurrentTask(DarkRaftTableAnalysisTask):
    """Analyze some dark data"""

    ConfigClass = DarkCurrentConfig
    _DefaultName = "DarkCurrentTask"

    intablename_format = SUPERDARK_FORMATTER

    def extract(self, butler, data, **kwargs):
        """Extract data

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
            output data tables
        """
        self.safe_update(**kwargs)

        slots = ALL_SLOTS

        if butler is not None:
            self.log.warn("Ignoring butler")

        dark_current_data = dict(median=[],
                                 stdev=[],
                                 mean=[],
                                 fit_mean=[],
                                 fit_width=[],
                                 fit_dof=[],
                                 fit_chi2=[],
                                 exptime=[],
                                 current=[],
                                 slot=[],
                                 amp=[])

        self.log_info_raft_msg(self.config, "")

        for islot, slot in enumerate(slots):

            self.log_progress("  %s" % slot)

            mask_files = self.get_mask_files(slot=slot)
            superdark_file = data[slot].replace('.fits.fits', '.fits')
            superdark_frame = get_ccd_from_id(None, superdark_file, mask_files)
            exptime = get_exposure_time(None, superdark_frame)

            amps = get_amp_list(None, superdark_frame)
            for iamp, amp in enumerate(amps):
                regions = get_geom_regions(None, superdark_frame, amp)
                imaging = regions['imaging']
                superdark_im = get_raw_image(None, superdark_frame, amp)
                image_data = superdark_im[imaging].array
                median = np.median(image_data)
                stdev = np.std(image_data)
                hist_bins = np.linspace(median - 5 * stdev, median + 5 * stdev, 101)
                hist = np.histogram(image_data, bins=hist_bins)
                fit_result = gauss_fit(hist)
                fit_pars = fit_result[0]
                dark_current_data['median'].append(median)
                dark_current_data['stdev'].append(stdev)
                dark_current_data['mean'].append(np.mean(image_data))
                dark_current_data['fit_mean'].append(fit_pars[1])
                dark_current_data['fit_width'].append(fit_pars[2])
                dark_current_data['fit_dof'].append(0.)
                dark_current_data['fit_chi2'].append(0.)
                dark_current_data['exptime'].append(exptime)
                dark_current_data['current'].append(median/exptime)
                dark_current_data['slot'].append(islot)
                dark_current_data['amp'].append(iamp)

        self.log_progress("Done!")

        dtables = TableDict()
        dtables.make_datatable('dark_current', dark_current_data)

        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Make plots

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

        dtable = dtables['dark_current']
        figs.plot_raft_amp_values('dark_current',
                                  dtable['current'],
                                  xlabel='Amplifier',
                                  ylabel='Current [ADU/s]',
                                  slots=ALL_SLOTS)


class DarkCurrentSummaryConfig(DarkSummaryAnalysisConfig):
    """Configuration for DarkCurrentSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='dark_current')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='dark_current_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class DarkCurrentSummaryTask(DarkSummaryAnalysisTask):
    """Summarize the analysis results for many runs"""

    ConfigClass = DarkCurrentSummaryConfig
    _DefaultName = "DarkCurrentSummaryTask"

    def extract(self, butler, data, **kwargs):
        """Extract data

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
            Output data tables
        """
        self.safe_update(**kwargs)

        for key, val in data.items():
            data[key] = val.replace(self.config.outsuffix, self.config.insuffix)

        # Define the set of columns to keep and remove
        # keep_cols = []
        # remove_cols = []

        outtable = vstack_tables(data, tablename='dark_current')

        dtables = TableDict()
        dtables.add_datatable('stats', outtable)
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
        sumtable = dtables['stats']
        runtable = dtables['runs']

        yvals = sumtable['current']
        yerrs = (sumtable['stdev'] / sumtable['exptime']).clip(0., 0.05)

        runs = runtable['runs']

        figs.plot_run_chart("stats", runs, yvals, yerrs=yerrs, ylabel="Dark Current [ADU/s]")
        #figs.plot_run_chart("stats", runs, yvals, ylabel="Dark Current [ADU/s]")


EO_TASK_FACTORY.add_task_class('DarkCurrent', DarkCurrentTask)
EO_TASK_FACTORY.add_task_class('DarkCurrentSummary', DarkCurrentSummaryTask)
