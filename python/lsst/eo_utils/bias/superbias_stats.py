"""Class to analyze the variation in the bias images"""

import sys

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_raw_image, get_amp_list

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .analysis import BiasAnalysisConfig, BiasAnalysisTask, BiasAnalysisByRaft

from .file_utils import RAFT_BIAS_TABLE_FORMATTER, RAFT_BIAS_PLOT_FORMATTER,\
    SUM_SBIAS_TABLE_FORMATTER, SUM_SBIAS_PLOT_FORMATTER

from .meta_analysis import SuperbiasSummaryByRaft, BiasSummaryAnalysisConfig,\
    BiasSummaryAnalysisTask


class SuperbiasStatsConfig(BiasAnalysisConfig):
    """Configuration for SuperbiasStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='stats')
    bias = EOUtilOptions.clone_param('bias')
    mask = EOUtilOptions.clone_param('mask')
    stat = EOUtilOptions.clone_param('stat')


class SuperbiasStatsTask(BiasAnalysisTask):
    """Analyze the variation in the bias images"""

    ConfigClass = SuperbiasStatsConfig
    _DefaultName = "SuperbiasStatsTask"
    iteratorClass = BiasAnalysisByRaft

    tablename_format = RAFT_BIAS_TABLE_FORMATTER
    plotname_format = RAFT_BIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor"""
        BiasAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs:
        raft (str)                 Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)              Run number, i.e,. '6106D'
        outdir (str)               Output directory
        """
        self.safe_update(**kwargs)
        slots = ALL_SLOTS

        if butler is not None:
            sys.stdout.write("Ignoring butler in superbias_stats.extract\n")
        if data is not None:
            sys.stdout.write("Ignoring raft_data in superbias_stats.extract\n")

        stats_data = {}

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(slots):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            mask_files = self.get_mask_files(slot=slot)
            superbias = self.get_superbias_frame(mask_files, slot=slot)
            self.get_superbias_stats(None, superbias, stats_data, islot)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, slots))
        dtables.make_datatable('slots', dict(slots=slots))
        dtables.make_datatable('stats', stats_data)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the stats on the superbias frames

        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
        """
        data = dtables.get_table('stats')

        figs.plot_stat_color("mean", data['mean'], clabel="Mean of STD [ADU]")
        figs.plot_stat_color("std", data['std'], clabel="STD of STD [ADU]")


    @staticmethod
    def get_superbias_stats(butler, superbias, stats_data, islot):
        """Get the serial overscan data

        @param butler (`Butler)         The data butler
        @param superbias (`MaskedCCD)   The ccd we are getting data from
        @param stats_data (dict)       The dictionary we are filling
        @param kwargs:
        islot (int)              Index of the slot in question
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


class SuperbiasSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='sum')
    dataset = EOUtilOptions.clone_param('dataset')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    stat = EOUtilOptions.clone_param('stat')


class SuperbiasSummaryTask(BiasSummaryAnalysisTask):
    """Summarize the results for the analysis of variations of the bias frames"""

    ConfigClass = SuperbiasSummaryConfig
    _DefaultName = "SuperbiasSummaryTask"
    iteratorClass = SuperbiasSummaryByRaft

    tablename_format = SUM_SBIAS_TABLE_FORMATTER
    plotname_format = SUM_SBIAS_PLOT_FORMATTER

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

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
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
