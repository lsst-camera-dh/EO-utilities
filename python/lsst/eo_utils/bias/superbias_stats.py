"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import STANDARD_RAFT_ARGS

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_raw_image, get_amp_list

from .analysis import BiasAnalysisFunc, BiasAnalysisByRaft

from .file_utils import raft_superbias_tablename, raft_superbias_plotname,\
    get_superbias_frame, superbias_summary_tablename, superbias_summary_plotname


from .meta_analysis import SuperbiasSummaryByRaft, BiasSummaryAnalysisFunc


class superbias_stats(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_RAFT_ARGS + ['stat', 'mask', 'bias']
    analysisClass = BiasAnalysisByRaft
    tablename_func = raft_superbias_tablename
    plotname_func = raft_superbias_plotname

    def __init__(self):
        """C'tor"""
        BiasAnalysisFunc.__init__(self, "stats")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs:
        raft (str)                 Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)              Run number, i.e,. '6106D'
        outdir (str)               Output directory
        """
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
            superbias = get_superbias_frame(mask_files=mask_files, **kwcopy)
            superbias_stats.get_superbias_stats(None, superbias, stats_data,
                                                islot=islot, slot=slot)

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, slots))
        dtables.make_datatable('slots', dict(slots=slots))
        dtables.make_datatable('stats', stats_data)
        return dtables


    @staticmethod
    def plot(dtables, figs):
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



class superbias_stats_summary(BiasSummaryAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = ['dataset']
    iteratorClass = SuperbiasSummaryByRaft
    tablename_func = superbias_summary_tablename
    plotname_func = superbias_summary_plotname

    def __init__(self):
        """C'tor"""
        BiasSummaryAnalysisFunc.__init__(self, "stats")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Make a summry table of the bias FFT data

        @param filedict (dict)      The files we are analyzing
        @param kwargs
            bias (str)
            superbias (str)

        @returns (TableDict)
        """
        if butler is not None:
            sys.stdout.write("Ignoring butler in superbias_stats_summary.extract %s\n" % kwargs)

        outtable = vstack_tables(data, tablename='stats')

        dtables = TableDict()
        dtables.add_datatable('stats', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    @staticmethod
    def plot(dtables, figs):
        """Plot the summary data from the superbias statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        sumtable = dtables['stats']
        runtable = dtables['runs']
        yvals = sumtable['mean'].flatten().clip(0., 30.)
        yerrs = sumtable['std'].flatten().clip(0., 10.)
        runs = runtable['runs']

        figs.plot_run_chart("stats", runs, yvals, yerrs=yerrs, ylabel="Superbias STD [ADU]")
