"""Functions to analyse summary data from bias and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import TableAnalysisBySlot,\
    TableAnalysisByRaft, SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.file_utils import SUPERBIAS_FORMATTER

from .file_utils import SLOT_BIAS_TABLE_FORMATTER,\
    RAFT_BIAS_TABLE_FORMATTER, RAFT_BIAS_PLOT_FORMATTER,\
    RAFT_SBIAS_TABLE_FORMATTER, RAFT_SBIAS_PLOT_FORMATTER,\
    SUM_BIAS_TABLE_FORMATTER, SUM_BIAS_PLOT_FORMATTER,\
    SLOT_SBIAS_TABLE_FORMATTER, SLOT_SBIAS_PLOT_FORMATTER,\
    SUM_SBIAS_TABLE_FORMATTER, SUM_SBIAS_PLOT_FORMATTER


class BiasRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slots = EOUtilOptions.clone_param('slots')
    infilekey = EOUtilOptions.clone_param('infilekey')


class BiasRaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = BiasRaftTableAnalysisConfig
    _DefaultName = "BiasRaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_BIAS_TABLE_FORMATTER
    tablename_format = RAFT_BIAS_TABLE_FORMATTER
    plotname_format = RAFT_BIAS_PLOT_FORMATTER
    datatype = 'bias'



class BiasSummaryAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class BiasSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = BiasSummaryAnalysisConfig
    _DefaultName = "BiasSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_BIAS_TABLE_FORMATTER
    tablename_format = SUM_BIAS_TABLE_FORMATTER
    plotname_format = SUM_BIAS_PLOT_FORMATTER
    datatype = 'bias'


class SuperbiasSlotTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    infilekey = EOUtilOptions.clone_param('infilekey')


class SuperbiasSlotTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SuperbiasSlotTableAnalysisConfig
    _DefaultName = "SuperbiasSlotTableAnalysisTask"
    iteratorClass = TableAnalysisBySlot

    intablename_format = SUPERBIAS_FORMATTER
    tablename_format = SLOT_SBIAS_TABLE_FORMATTER
    plotname_format = SLOT_SBIAS_PLOT_FORMATTER

    datatype = 'superbias'


class SuperbiasRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slots = EOUtilOptions.clone_param('slots')
    infilekey = EOUtilOptions.clone_param('infilekey')


class SuperbiasRaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = BiasRaftTableAnalysisConfig
    _DefaultName = "BiasRaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SUPERBIAS_FORMATTER
    tablename_format = RAFT_SBIAS_TABLE_FORMATTER
    plotname_format = RAFT_SBIAS_PLOT_FORMATTER

    datatype = 'superbias'



class SuperbiasSummaryAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


class SuperbiasSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SuperbiasSummaryAnalysisConfig
    _DefaultName = "SuperbiasSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_SBIAS_TABLE_FORMATTER
    tablename_format = SUM_SBIAS_TABLE_FORMATTER
    plotname_format = SUM_SBIAS_PLOT_FORMATTER

    datatype = 'superbias'
