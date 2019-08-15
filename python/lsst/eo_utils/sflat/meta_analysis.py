"""Functions to analyse summary data from superflat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import TableAnalysisBySlot,\
    TableAnalysisByRaft, SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SUM_SFLAT_TABLE_FORMATTER,\
    SUM_SFLAT_PLOT_FORMATTER,\
    SLOT_SFLAT_TABLE_FORMATTER, SLOT_SFLAT_PLOT_FORMATTER,\
    RAFT_SFLAT_TABLE_FORMATTER, RAFT_SFLAT_PLOT_FORMATTER

class SflatSlotTableAnalysisConfig(AnalysisConfig):
    """Configuration for superflat analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    insuffix = EOUtilOptions.clone_param('insuffix')


class SflatSlotTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard superflat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SflatSlotTableAnalysisConfig
    _DefaultName = "SflatSlotTableAnalysisTask"
    iteratorClass = TableAnalysisBySlot

    intablename_format = SLOT_SFLAT_TABLE_FORMATTER
    tablename_format = SLOT_SFLAT_TABLE_FORMATTER
    plotname_format = SLOT_SFLAT_PLOT_FORMATTER
    datatype = 'sflat table'


class SflatRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for superflat analyses"""
    insuffix = EOUtilOptions.clone_param('insuffix')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slots = EOUtilOptions.clone_param('slots')


class SflatRaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard superflat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SflatRaftTableAnalysisConfig
    _DefaultName = "SflatRaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_SFLAT_TABLE_FORMATTER
    tablename_format = RAFT_SFLAT_TABLE_FORMATTER
    plotname_format = RAFT_SFLAT_PLOT_FORMATTER
    datatype = 'sflat table'


class SflatSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class SflatSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard sflat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SflatSummaryAnalysisConfig
    _DefaultName = "SflatSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_SFLAT_TABLE_FORMATTER
    tablename_format = SUM_SFLAT_TABLE_FORMATTER
    plotname_format = SUM_SFLAT_PLOT_FORMATTER
    datatype = 'sflat table'
