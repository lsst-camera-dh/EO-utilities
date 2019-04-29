"""Functions to analyse summary data from bias and superbias frames"""

import sys

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.file_utils import read_runlist

from lsst.eo_utils.base.iter_utils import AnalysisIterator,\
    SummaryAnalysisIterator, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SUM_BIAS_TABLE_FORMATTER, SUM_BIAS_PLOT_FORMATTER,\
    RAFT_BIAS_TABLE_FORMATTER, SLOT_BIAS_TABLE_FORMATTER, RAFT_SBIAS_TABLE_FORMATTER


def get_tablenames_by_raft(caller, butler, run, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param butler (`Butler`)    The data butler
    @param run_num (str)        The run number
    @param kwargs:
        bias (str)
        superbias (str)
    """
    kwcopy = kwargs.copy()
    kwcopy['run'] = run

    out_dict = {}
    raft_list = AnalysisIterator.get_raft_list(butler, run)

    for raft in raft_list:
        kwcopy['raft'] = raft
        slot_dict = {}
        for slot in ALL_SLOTS:
            kwcopy['slot'] = slot
            basename = SLOT_BIAS_TABLE_FORMATTER(caller, **kwcopy)
            datapath = basename + '.fits'
            slot_dict[slot] = datapath
        out_dict[raft] = slot_dict
    return out_dict


def get_raft_bias_tablefiles(caller, butler, dataset, **kwargs):
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
        run = runinfo[1]
        run_key = "%s_%s" % (raft, run)
        kwcopy['run'] = run
        kwcopy['raft'] = raft
        filedict[run_key] = RAFT_BIAS_TABLE_FORMATTER(caller, **kwcopy) + '.fits'

    return filedict


def get_raft_superbias_tablefiles(caller, butler, dataset, **kwargs):
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
    kwcopy.setdefault('superbias', kwargs.get('bias'))

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run = runinfo[1]
        run_key = "%s_%s" % (raft, run)
        kwcopy['run'] = run
        kwcopy['raft'] = raft
        filedict[run_key] = RAFT_SBIAS_TABLE_FORMATTER(caller, **kwcopy) + '.fits'

    return filedict


class BiasTableAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis function over all the slots in a raft"""

    get_data = get_tablenames_by_raft

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisByRaft.__init__(self, task)


class BiasSummaryByRaft(SummaryAnalysisIterator):
    """Small class to iterate an analysis function over all the slots in a raft"""

    get_data = get_raft_bias_tablefiles

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        SummaryAnalysisIterator.__init__(self, task)


class SuperbiasSummaryByRaft(SummaryAnalysisIterator):
    """Small class to iterate an analysis task over all the raft and then all the slots in a raft"""

    get_data = get_raft_superbias_tablefiles

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        SummaryAnalysisIterator.__init__(self, task)



class BiasSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class BiasSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = BiasSummaryAnalysisConfig
    _DefaultName = "BiasSummaryAnalysisTask"
    iteratorClass = BiasSummaryByRaft

    tablename_format = SUM_BIAS_TABLE_FORMATTER
    plotname_format = SUM_BIAS_PLOT_FORMATTER

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
