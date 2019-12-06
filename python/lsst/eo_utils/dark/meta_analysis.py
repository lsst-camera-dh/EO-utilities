"""Functions to analyse summary data from bias and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft,\
    SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.dark.file_utils import SLOT_DARK_TABLE_FORMATTER,\
    SUM_DARK_TABLE_FORMATTER, SUM_DARK_PLOT_FORMATTER,\
    RAFT_DARK_TABLE_FORMATTER, RAFT_DARK_PLOT_FORMATTER,\
    SUM_SDARK_TABLE_FORMATTER, SUM_SDARK_PLOT_FORMATTER,\
    RAFT_SDARK_TABLE_FORMATTER, RAFT_SDARK_PLOT_FORMATTER


class DarkRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slots = EOUtilOptions.clone_param('slots')
    infilekey = EOUtilOptions.clone_param('infilekey')


class DarkRaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = DarkRaftTableAnalysisConfig
    _DefaultName = "DarkRaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_DARK_TABLE_FORMATTER
    tablename_format = RAFT_DARK_TABLE_FORMATTER
    plotname_format = RAFT_DARK_PLOT_FORMATTER

    datatype = 'dark'


class DarkSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class DarkSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard dark data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = DarkSummaryAnalysisConfig
    _DefaultName = "DarkSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_DARK_TABLE_FORMATTER
    tablename_format = SUM_DARK_TABLE_FORMATTER
    plotname_format = SUM_DARK_PLOT_FORMATTER

    datatype = 'dark'


class SuperdarkSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class SuperdarkSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard dark data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SuperdarkSummaryAnalysisConfig
    _DefaultName = "SuperdarkSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_SDARK_TABLE_FORMATTER
    tablename_format = SUM_SDARK_TABLE_FORMATTER
    plotname_format = SUM_SDARK_PLOT_FORMATTER

    datatype = 'dark'
