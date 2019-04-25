"""Functions to analyse summary data from bias and superbias frames"""

import sys

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.file_utils import read_runlist

from lsst.eo_utils.base.iter_utils import AnalysisIterator,\
    SummaryAnalysisIterator, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.fe55.file_utils import slot_fe55_tablename,\
    slot_fe55_plotname, raft_fe55_tablename



def get_tablenames_by_raft(caller, butler, run_num, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param butler (`Butler`)    The data butler
    @param run_num (str)        The run number
    @param kwargs:
    """
    kwcopy = kwargs.copy()
    kwcopy['run'] = run_num

    out_dict = {}
    raft_list = AnalysisIterator.get_raft_list(butler, run_num)

    for raft in raft_list:
        kwcopy['raft'] = raft
        slot_dict = {}
        for slot in ALL_SLOTS:
            kwcopy['slot'] = slot
            basename = slot_fe55_tablename(caller, **kwcopy)
            datapath = basename + '.fits'
            slot_dict[slot] = datapath
        out_dict[raft] = slot_dict
    return out_dict


def get_raft_fe55_tablefiles(caller, butler, dataset, **kwargs):
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
        run = runinfo[1]
        run_key = "%s_%s" % (raft, run)
        kwcopy['run'] = run
        kwcopy['raft'] = raft
        filedict[run_key] = raft_fe55_tablename(caller, **kwcopy) + '.fits'

    return filedict



class Fe55TableAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis function over all the slots in a raft"""

    get_data = get_tablenames_by_raft

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisByRaft.__init__(self, task)


class Fe55SummaryByRaft(SummaryAnalysisIterator):
    """Small class to iterate an analysis function over all the slots in a raft"""

    get_data = get_raft_fe55_tablefiles

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        SummaryAnalysisIterator.__init__(self, task)


class Fe55SummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilConfig.clone_param('outdir')
    dataset = EOUtilConfig.clone_param('dataset')
    suffix = EOUtilConfig.clone_param('suffix')


class Fe55SummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard fe55 data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = Fe55SummaryAnalysisConfig
    _DefaultName = "Fe55SummaryAnalysisTask"
    iteratorClass = Fe55SummaryByRaft
    argnames = ['dataset', 'butler_repo']
    tablename_func = slot_fe55_tablename
    plotname_func = slot_fe55_plotname

    def __init__(self, **kwargs):
        """ C'tor
        @param kwargs:
        """
        AnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
