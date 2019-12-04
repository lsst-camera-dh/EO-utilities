"""Functions to analyse summary data from flat-field frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import TableAnalysisBySlot,\
    TableAnalysisByRaft, SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SUM_FLAT_TABLE_FORMATTER, SUM_FLAT_PLOT_FORMATTER,\
    SLOT_FLAT_TABLE_FORMATTER, SLOT_FLAT_PLOT_FORMATTER,\
    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER


class FlatSlotTableAnalysisConfig(AnalysisConfig):
    """Configuration for superflat analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    infilekey = EOUtilOptions.clone_param('infilekey')


class FlatSlotTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard superflat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = FlatSlotTableAnalysisConfig
    _DefaultName = "FlatSlotTableAnalysisTask"
    iteratorClass = TableAnalysisBySlot

    intablename_format = SLOT_FLAT_TABLE_FORMATTER
    tablename_format = SLOT_FLAT_TABLE_FORMATTER
    plotname_format = SLOT_FLAT_PLOT_FORMATTER
    datatype = 'flat table'


class FlatRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slots = EOUtilOptions.clone_param('slots')
    infilekey = EOUtilOptions.clone_param('infilekey')


class FlatRaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = FlatRaftTableAnalysisConfig
    _DefaultName = "FlatRaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_FLAT_TABLE_FORMATTER
    tablename_format = RAFT_FLAT_TABLE_FORMATTER
    plotname_format = RAFT_FLAT_PLOT_FORMATTER
    datatype = 'flat table'


class FlatSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for flat analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class FlatSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard flat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = FlatSummaryAnalysisConfig
    _DefaultName = "FlatSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_FLAT_TABLE_FORMATTER
    tablename_format = SUM_FLAT_TABLE_FORMATTER
    plotname_format = SUM_FLAT_PLOT_FORMATTER

    datatype = 'flat table'
