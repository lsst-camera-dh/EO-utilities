"""Functions to analyse summary data from bias and superbias frames"""

import sys

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.file_utils import read_runlist

from lsst.eo_utils.base.iter_utils import AnalysisIterator,\
    SummaryAnalysisIterator, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisFunc

from .file_utils import slot_fe55_tablename,\
    slot_fe55_plotname, raft_fe55_tablename, raft_fe55_plotname



def get_tablenames_by_raft(butler, run_num, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param butler (`Butler`)    The data butler
    @param run_num (str)        The run number
    @param kwargs:
    """
    kwcopy = kwargs.copy()
    kwcopy['run_num'] = run_num

    out_dict = {}
    raft_list = AnalysisIterator.get_raft_list(butler, run_num)

    for raft in raft_list:
        kwcopy['raft'] = raft
        slot_dict = {}
        for slot in ALL_SLOTS:
            kwcopy['slot'] = slot
            kwcopy['fileType'] = 'fe55'
            kwcopy['testType'] = ''
            basename = slot_fe55_tablename(**kwcopy)
            datapath = basename + '.fits'
            slot_dict[slot] = datapath
        out_dict[raft] = slot_dict
    return out_dict


def get_raft_fe55_tablefiles(butler, dataset, **kwargs):
    """Extract the statistics of the FFT of the fe55

    @param butler (`Butler`)    The data butler
    @param dataset (str)
    @param kwargs:

    @returns (dict) mapping runkey to filename
    """
    if butler is not None:
        sys.stdout.write("Ignoring butler in get_raft_fe55_tablefiles\n")

    infile = '%s_runs.txt' % dataset

    run_list = read_runlist(infile)
    kwcopy = kwargs.copy()

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]
        run_key = "%s_%s" % (raft, run_num)
        kwcopy['run_num'] = run_num
        kwcopy['raft'] = raft
        filedict[run_key] = raft_fe55_tablename(**kwcopy) + '.fits'

    return filedict



class Fe55TableAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis function over all the slots in a raft"""

    data_func = get_tablenames_by_raft

    def __init__(self, analysis_func, argnames):
        """C'tor
        
        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisByRaft.__init__(self, analysis_func, argnames)


class Fe55SummaryByRaft(SummaryAnalysisIterator):
    """Small class to iterate an analysis function over all the slots in a raft"""

    data_func = get_raft_fe55_tablefiles

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        SummaryAnalysisIterator.__init__(self, analysis_func, argnames)


class Fe55SummaryAnalysisFunc(AnalysisFunc):
    """Simple functor class to tie together standard fe55 data analysis
    """

    # These can overridden by the sub-class
    iteratorClass = Fe55SummaryByRaft
    argnames = ['dataset', 'butler_repo']
    tablename_func = slot_fe55_tablename
    plotname_func = slot_fe55_plotname

    def __init__(self, datasuffix=""):
        """ C'tor
        @param datasuffix (str)        Suffix for filenames
        @param kwargs:
        """
        AnalysisFunc.__init__(self, datasuffix)
