"""Functions to analyse summary data from ppump analyses frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft,\
    SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.ppump.file_utils import SLOT_PPUMP_TABLE_FORMATTER,\
    SUM_PPUMP_TABLE_FORMATTER, SUM_PPUMP_PLOT_FORMATTER,\
    RAFT_PPUMP_TABLE_FORMATTER, RAFT_PPUMP_PLOT_FORMATTER


class PpumpRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    infilekey = EOUtilOptions.clone_param('infilekey')


class PpumpRaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = PpumpRaftTableAnalysisConfig
    _DefaultName = "PpumpRaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_PPUMP_TABLE_FORMATTER
    tablename_format = RAFT_PPUMP_TABLE_FORMATTER
    plotname_format = RAFT_PPUMP_PLOT_FORMATTER
    datatype = 'ppump table'


class PpumpSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class PpumpSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard ppump data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = PpumpSummaryAnalysisConfig
    _DefaultName = "PpumpSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_PPUMP_TABLE_FORMATTER
    tablename_format = SUM_PPUMP_TABLE_FORMATTER
    plotname_format = SUM_PPUMP_PLOT_FORMATTER

    datatype = 'ppump table'
