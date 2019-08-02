"""Functions to analyse fe55 and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.data_access import get_data_for_run

from .file_utils import SLOT_FE55_TABLE_FORMATTER,\
    SLOT_FE55_PLOT_FORMATTER


class Fe55AnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    nfiles = EOUtilOptions.clone_param('nfiles')


class Fe55AnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard fe55 data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = Fe55AnalysisConfig
    _DefaultName = "Fe55AnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_FE55_TABLE_FORMATTER
    plotname_format = SLOT_FE55_PLOT_FORMATTER
    datatype = 'fe55'
    testtypes = ['FE55']
