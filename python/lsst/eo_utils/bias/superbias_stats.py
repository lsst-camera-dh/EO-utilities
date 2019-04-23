"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_raw_image, get_amp_list

from .analysis import BiasAnalysisConfig, BiasAnalysisTask, BiasAnalysisByRaft

from .file_utils import raft_superbias_tablename, raft_superbias_plotname,\
    get_superbias_frame, superbias_summary_tablename, superbias_summary_plotname


from .meta_analysis import SuperbiasSummaryByRaft, BiasSummaryAnalysisConfig,\
    BiasSummaryAnalysisTask


class SuperbiasStatsConfig(BiasAnalysisConfig):
    """Configuration for SuperbiasStatsTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='stats')
    bias = EOUtilConfig.clone_param('bias')
    mask = EOUtilConfig.clone_param('mask')
    stat = EOUtilConfig.clone_param('stat')


class SuperbiasStatsTask(BiasAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = SuperbiasStatsConfig
    _DefaultName = "SuperbiasStatsTask"
    iteratorClass = BiasAnalysisByRaft
    tablefile_name = raft_superbias_tablename
    plotfile_name = raft_superbias_plotname

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

        kwcopy = kwargs.copy()
        if butler is not None:
            sys.stdout.write("Ignoring butler in superbias_stats.extract")
        if data is not None:
            sys.stdout.write("Ignoring raft_data in superbias_stats.extract")

        stats_data = {}
        for islot, slot in enumerate(slots):
            kwcopy['slot'] = slot
            mask_files = get_mask_files(**kwcopy)
            superbias = get_superbias_frame(self, mask_files=mask_files, **kwcopy)
            self.get_superbias_stats(None, superbias, stats_data,
                                     islot=islot, slot=slot)

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
    def get_superbias_stats(butler, superbias, stats_data, **kwargs):
        """Get the serial overscan data

        @param butler (`Butler)         The data butler
        @param superbias (`MaskedCCD)   The ccd we are getting data from
        @param stats_data (dict)       The dictionary we are filling
        @param kwargs:
        islot (int)              Index of the slot in question
        """
        amps = get_amp_list(butler, superbias)
        islot = kwargs.get('islot')

        if 'mean' not in stats_data:
            stats_data['mean'] = np.ndarray((9, 16))
            stats_data['median'] = np.ndarray((9, 16))
            stats_data['std'] = np.ndarray((9, 16))
            stats_data['min'] = np.ndarray((9, 16))
            stats_data['max'] = np.ndarray((9, 16))

        for i, amp in enumerate(amps):
            im = get_raw_image(butler, superbias, amp)
            stats_data['mean'][islot, i] = im.array.mean()
            stats_data['median'][islot, i] = np.median(im.array)
            stats_data['std'][islot, i] = im.array.std()
            stats_data['min'][islot, i] = im.array.min()
            stats_data['max'][islot, i] = im.array.max()


class SuperbiasSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='_stats_sum')
    dataset = EOUtilConfig.clone_param('dataset')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')


class SuperbiasSummaryTask(BiasSummaryAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = SuperbiasSummaryConfig
    _DefaultName = "SuperbiasSummaryTask"
    iteratorClass = SuperbiasSummaryByRaft
    tablefile_name = superbias_summary_tablename
    plotfile_name = superbias_summary_plotname

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
            sys.stdout.write("Ignoring butler in superbias_stats_summary.extract %s\n" % kwargs)

        for key, val in data.items():
            data[key] = val.replace('.fits', '_stdevclip_stats.fits')

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
