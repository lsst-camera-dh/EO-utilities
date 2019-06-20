"""Functions to analyse summary data from flat-field frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft,\
    SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    SUM_FLAT_TABLE_FORMATTER, SUM_FLAT_PLOT_FORMATTER,\
    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER

class FlatRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slots = EOUtilOptions.clone_param('slots')
    insuffix = EOUtilOptions.clone_param('insuffix')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


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


class FlatSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for flat analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


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
