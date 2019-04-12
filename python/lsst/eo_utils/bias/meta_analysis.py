"""Functions to analyse summary data from bias and superbias frames"""

import sys

from lsst.eo_utils.base.file_utils import read_runlist

from lsst.eo_utils.base.iter_utils import AnalysisIterator, SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisFunc

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


def get_raft_bias_tablefiles(butler, dataset, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param butler (`Butler`)    The data butler
    @param dataset (str)
    @param kwargs:
        bias (str)
        superbias (str)

    @returns (dict) mapping runkey to filename
    """
    if butler is not None:
        sys.stdout.write("Ignoring butler in get_raft_bias_tablefiles\n")

    infile = '%s_runs.txt' % dataset

    run_list = read_runlist(infile)
    kwcopy = kwargs.copy()

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]
        run_key = "%s_%s" % (raft, run_num)
        kwcopy['run'] = run_num
        kwcopy['raft'] = raft
        filedict[run_key] = raft_bias_tablename(**kwcopy) + '.fits'

    return filedict


def get_raft_superbias_tablefiles(butler, dataset, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param butler (`Butler`)    The data butler
    @param dataset (str)
    @param kwargs:
        bias (str)
        superbias (str)

    @returns (dict) mapping runkey to filename
    """
    if butler is not None:
        sys.stdout.write("Ignoring butler in get_raft_superbias_tablefiles\n")

    infile = '%s_runs.txt' % dataset

    run_list = read_runlist(infile)
    kwcopy = kwargs.copy()

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]
        run_key = "%s_%s" % (raft, run_num)
        kwcopy['run'] = run_num
        kwcopy['raft'] = raft
        filedict[run_key] = raft_superbias_tablename(**kwargs) + '.fits'

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



class BiasSummaryAnalysisFunc(AnalysisFunc):
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
        AnalysisFunc.__init__(self, datasuffix)
