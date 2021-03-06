"""Base classes for tasks to analyze bias and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SLOT_BIAS_TABLE_FORMATTER, SLOT_BIAS_PLOT_FORMATTER


class BiasAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    nfiles = EOUtilOptions.clone_param('nfiles', default=10)


class BiasAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """
    # These can overridden by the sub-class
    ConfigClass = BiasAnalysisConfig
    _DefaultName = "BiasAnalysis"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_BIAS_TABLE_FORMATTER
    plotname_format = SLOT_BIAS_PLOT_FORMATTER

    # Overide these
    datatype = 'bias'
    imagetype = 'bias'
