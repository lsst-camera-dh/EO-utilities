"""Functions to analyse summary data from fe55 analyses"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft,\
    SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SLOT_FE55_TABLE_FORMATTER,\
    RAFT_FE55_TABLE_FORMATTER, RAFT_FE55_PLOT_FORMATTER,\
    SUM_FE55_TABLE_FORMATTER, SUM_FE55_PLOT_FORMATTER


class Fe55RaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    infilekey = EOUtilOptions.clone_param('infilekey')


class Fe55RaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = Fe55RaftTableAnalysisConfig
    _DefaultName = "Fe55RaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_FE55_TABLE_FORMATTER
    tablename_format = RAFT_FE55_TABLE_FORMATTER
    plotname_format = RAFT_FE55_PLOT_FORMATTER

    datatype = 'fe55 table'


class Fe55SummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class Fe55SummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard fe55 data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = Fe55SummaryAnalysisConfig
    _DefaultName = "Fe55SummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_FE55_TABLE_FORMATTER
    tablename_format = SUM_FE55_TABLE_FORMATTER
    plotname_format = SUM_FE55_PLOT_FORMATTER

    datatype = 'fe55 table'
