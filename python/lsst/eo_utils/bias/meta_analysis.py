"""Functions to analyse summary data from bias and superbias frames"""

import sys

from lsst.eo_utils.base.file_utils import read_runlist, makedir_safe
from lsst.eo_utils.base.data_utils import TableDict
from lsst.eo_utils.base.plot_utils import FigureDict
from lsst.eo_utils.base.iter_utils import AnalysisIterator, SummaryAnalysisIterator

from .file_utils import slot_bias_tablename,\
    slot_bias_plotname, raft_bias_tablename, raft_superbias_tablename

SLOT_LIST = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']


def get_tablenames_by_slot(butler, run_num, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param rum_num (str)     The run number
    @param raft_list (list)  The raft names
    @param kwargs:
        bias (str)
        superbias (str)
    """
    kwcopy = kwargs.copy()
    kwcopy['run'] = run_num

    out_dict = {}
    raft_list = AnalysisIterator.get_raft_list(butler, run_num)

    for raft in raft_list:
        kwcopy['raft'] = raft
        slot_dict = {}
        for slot in SLOT_LIST:
            kwcopy['slot'] = slot
            basename = slot_bias_tablename(**kwcopy)
            datapath = basename + '.fits'
            slot_dict[slot] = datapath
        out_dict[raft] = slot_dict
    return out_dict


def get_raft_bias_tablefiles(dataset, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param dataset (str)
    @param kwargs:
        bias (str)
        superbias (str)

    @returns (dict) mapping runkey to filename
    """
    infile = '%s_runs.txt' % dataset

    run_list = read_runlist(infile)

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]
        run_key = "%s_%s" % (raft, run_num)
        filedict[run_key] = raft_bias_tablename('analysis', raft, run_num, **kwargs) + '.fits'

    return filedict


def get_raft_superbias_tablefiles(dataset, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param dataset (str)
    @param kwargs:
        bias (str)
        superbias (str)

    @returns (dict) mapping runkey to filename
    """
    infile = '%s_runs.txt' % dataset

    run_list = read_runlist(infile)

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]
        run_key = "%s_%s" % (raft, run_num)
        filedict[run_key] = raft_superbias_tablename('analysis', raft, run_num, **kwargs) + '.fits'

    return filedict



class BiasSummaryByRaft(SummaryAnalysisIterator):
    """Small class to iterate an analysis function over all the slots in a raft"""

    data_func = get_raft_bias_tablefiles

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        SummaryAnalysisIterator.__init__(self, analysis_func, argnames)


class SuperbiasSummaryByRaft(SummaryAnalysisIterator):
    """Small class to iterate an analysis task over all the raft and then all the slots in a raft"""

    data_func = get_raft_superbias_tablefiles

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        SummaryAnalysisIterator.__init__(self, analysis_func, argnames)



class BiasSummaryAnalysisFunc:
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    iteratorClass = BiasSummaryByRaft
    argnames = []
    tablename_func = slot_bias_tablename
    plotname_func = slot_bias_plotname

    def __init__(self, datasuffix=""):
        """ C'tor
        @param datasuffix (str)        Suffix for filenames
        @param kwargs:
        """
        self.datasuffix = datasuffix

    @classmethod
    def make_datatables(cls, filedict, datasuffix, **kwargs):
        """Tie together the functions to make the data tables
        @param filedict (dict)         Dictionary pointing to the bias and mask files
        @param datasuffix (str)        Suffix for filenames
        @param kwargs

        @return (TableDict)
        """
        kwargs['suffix'] = datasuffix
        tablebase = cls.tablename_func(**kwargs)
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if kwargs.get('skip', False):
            dtables = TableDict(output_data)
        else:
            dtables = cls.extract(filedict, **kwargs)
            dtables.save_datatables(output_data)
        return dtables

    @classmethod
    def make_plots(self, dtables, **kwargs):
        """Tie together the functions to make the data tables
        @param dtables (`TableDict`)   The data tables

        @return (`FigureDict`) the figues we produced
        """
        figs = FigureDict()
        self.plot(dtables, figs)
        if kwargs.get('interactive', False):
            figs.save_all(None)
            return figs
        plotbase = cls.plotname_func(**kwargs)
        makedir_safe(plotbase)
        figs.save_all(plotbase)
        return None

    def __call__(self, dataset, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        dtables = self.make_datatables(dataset, **kwargs)
        if kwargs.get('plot', False):
            figs = self.make_plots(dtables, **kwargs)

    @classmethod
    def make(cls, dataset, **kwargs):
        """Tie together the functions
        @param dataset (str)       Key for the data we are analyzing
        @param kwargs              Passed to the functions that do the actual work
        """
        obj = cls()
        obj(dataset, **kwargs)

    @classmethod
    def run(cls):
        """Run the analysis"""
        functor = cls.iteratorClass(cls.make, cls.argnames)
        functor.run()

    @staticmethod
    def extract(filedict, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("BiasAnalysisFunc.extract")

    @staticmethod
    def plot(dtables, figs):
        """This needs to be implemented by the sub-class"""
        if dtables is not None and figs is not None:
            sys.stdout.write("Warning, plotting function not implemented\n")
