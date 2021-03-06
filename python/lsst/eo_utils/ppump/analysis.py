"""Functions to analyse ppump and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SLOT_PPUMP_TABLE_FORMATTER,\
    SLOT_PPUMP_PLOT_FORMATTER

class PpumpAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    nfiles = EOUtilOptions.clone_param('nfiles')


class PpumpAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard ppump data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = PpumpAnalysisConfig
    _DefaultName = "PpumpAnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_PPUMP_TABLE_FORMATTER
    plotname_format = SLOT_PPUMP_PLOT_FORMATTER
    datatype = 'ppump'
    testtypes = ['PPUMP']
