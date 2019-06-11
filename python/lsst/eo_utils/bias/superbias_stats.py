"""Class to analyze the variation in the bias images"""

import sys

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.file_utils import SUPERBIAS_STAT_FORMATTER

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    get_raw_image, get_amp_list

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import RAFT_SBIAS_TABLE_FORMATTER, RAFT_SBIAS_PLOT_FORMATTER

from .meta_analysis import SuperbiasSummaryAnalysisConfig, SuperbiasSummaryAnalysisTask


class SuperbiasStatsConfig(AnalysisConfig):
    """Configuration for SuperbiasStatsTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    insuffix = EOUtilOptions.clone_param('insuffix', default='')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    stat = EOUtilOptions.clone_param('stat')
    mask = EOUtilOptions.clone_param('mask')
    stat = EOUtilOptions.clone_param('stat')


class SuperbiasStatsTask(AnalysisTask):
    """Analyze the variation in the bias images"""

    ConfigClass = SuperbiasStatsConfig
    _DefaultName = "SuperbiasStatsTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SUPERBIAS_STAT_FORMATTER
    tablename_format = RAFT_SBIAS_TABLE_FORMATTER
    plotname_format = RAFT_SBIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the statistics from the superbias frames

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
        slots = ALL_SLOTS

        if butler is not None:
            sys.stdout.write("Ignoring butler in superbias_stats.extract\n")

        stats_data = {}

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(slots):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            superbias_file = data[slot]
            mask_files = self.get_mask_files(slot=slot)

            superbias_frame = get_ccd_from_id(None, superbias_file, mask_files)
            self.get_superbias_stats(None, superbias_frame, stats_data, islot)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, slots))
        dtables.make_datatable('slots', dict(slots=slots))
        dtables.make_datatable('stats', stats_data)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the stats on the superbias frames

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        data = dtables.get_table('stats')

        figs.plot_stat_color("mean", data['mean'], clabel="Mean of STD [ADU]")
        figs.plot_stat_color("std", data['std'], clabel="STD of STD [ADU]")


    @staticmethod
    def get_superbias_stats(butler, superbias, stats_data, islot):
        """Get the serial overscan data

        Parameters
        ----------
        butler : `Butler`
            The data butler
        superbias : `MaskedCCD`
            The ccd we are getting data from
        stats_data : `dict`
            The data we are updating

        Keywords
        --------
        islot : `int`
            The slot index
        """
        amps = get_amp_list(butler, superbias)

        if 'mean' not in stats_data:
            stats_data['mean'] = np.ndarray((9, 16))
            stats_data['median'] = np.ndarray((9, 16))
            stats_data['std'] = np.ndarray((9, 16))
            stats_data['min'] = np.ndarray((9, 16))
            stats_data['max'] = np.ndarray((9, 16))

        for i, amp in enumerate(amps):
            img = get_raw_image(butler, superbias, amp)
            stats_data['mean'][islot, i] = img.array.mean()
            stats_data['median'][islot, i] = np.median(img.array)
            stats_data['std'][islot, i] = img.array.std()
            stats_data['min'][islot, i] = img.array.min()
            stats_data['max'][islot, i] = img.array.max()


class SuperbiasSummaryConfig(SuperbiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='sum')
    dataset = EOUtilOptions.clone_param('dataset')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    stat = EOUtilOptions.clone_param('stat')


class SuperbiasSummaryTask(SuperbiasSummaryAnalysisTask):
    """Summarize the results for the analysis of variations of the bias frames"""

    ConfigClass = SuperbiasSummaryConfig
    _DefaultName = "SuperbiasSummaryTask"

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SuperbiasSummaryAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Make a summary table of the superbias statistics

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
            sys.stdout.write("Ignoring butler in superbias_stats_summary.extract\n")

        for key, val in data.items():
            data[key] = val.replace('_sum.fits', '_stats.fits')

        outtable = vstack_tables(data, tablename='stats')

        dtables = TableDict()
        dtables.add_datatable('stats', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the superbias statistics study

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
        yvals = sumtable['mean'].flatten().clip(0., 30.)
        yerrs = sumtable['std'].flatten().clip(0., 10.)
        runs = runtable['runs']

        figs.plot_run_chart("stats", runs, yvals, yerrs=yerrs, ylabel="Superbias STD [ADU]")


EO_TASK_FACTORY.add_task_class('SuperbiasStats', SuperbiasStatsTask)
EO_TASK_FACTORY.add_task_class('SuperbiasSummary', SuperbiasSummaryTask)
