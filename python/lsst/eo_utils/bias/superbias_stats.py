"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.config_utils import STANDARD_RAFT_ARGS

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_raw_image, get_amp_list

from .analysis import BiasAnalysisFunc, BiasAnalysisByRaft

from .file_utils import raft_superbias_tablename, raft_superbias_plotname,\
    get_superbias_frame

DEFAULT_BIAS_TYPE = 'spline'

ALL_SLOTS = 'S00 S01 S02 S10 S11 S12 S20 S21 S22'.split()

class superbias_stats(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_RAFT_ARGS + ['stat', 'mask']
    analysisClass = BiasAnalysisByRaft

    def __init__(self):
        """C'tor"""
        BiasAnalysisFunc.__init__(self, "stats", self.extract, self.plot,
                                  tablename_func=raft_superbias_tablename,
                                  plotname_func=raft_superbias_plotname)

    @staticmethod
    def extract(butler, raft_data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

        @param butler (`Butler`)   The data butler
        @param raft_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs:
        raft (str)                 Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)              Run number, i.e,. '6106D'
        outdir (str)               Output directory
        """
        slots = ALL_SLOTS

        kwcopy = kwargs.copy()
        if butler is not None:
            sys.stdout.write("Ignoring butler in extract_superbias_stats_raft")
        if raft_data is not None:
            sys.stdout.write("Ignoring raft_data in extract_superbias_stats_raft")

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
