"""Functions to analyse summary data from  qe (Quantum efficiency) runs"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.file_utils import PD_CALIB_FORMATTER

from lsst.eo_utils.base.iter_utils import TableAnalysisBySlot,\
    TableAnalysisByRaft, SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SLOT_QE_TABLE_FORMATTER,\
    SLOT_QE_PLOT_FORMATTER,\
    SUM_QE_TABLE_FORMATTER, SUM_QE_PLOT_FORMATTER,\
    RAFT_QE_TABLE_FORMATTER, RAFT_QE_PLOT_FORMATTER


class QeSlotTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    insuffix = EOUtilOptions.clone_param('insuffix')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class QeSlotTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = QeSlotTableAnalysisConfig
    _DefaultName = "QeSlotTableAnalysisTask"
    iteratorClass = TableAnalysisBySlot

    intablename_format = SLOT_QE_TABLE_FORMATTER
    tablename_format = SLOT_QE_TABLE_FORMATTER
    plotname_format = SLOT_QE_PLOT_FORMATTER

    def get_pd_calib_file(self, **kwargs):
        """Get the name of the pd_calib for a particular run, raft...

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The filename
        """
        return self.get_filename_from_format(PD_CALIB_FORMATTER, '.dat', **kwargs)


class QeRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    insuffix = EOUtilOptions.clone_param('insuffix')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class QeRaftTableAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = QeSlotTableAnalysisConfig
    _DefaultName = "QeRaftTableAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_QE_TABLE_FORMATTER
    tablename_format = RAFT_QE_TABLE_FORMATTER
    plotname_format = RAFT_QE_PLOT_FORMATTER


class QeSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class QeSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard qe data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = QeSummaryAnalysisConfig
    _DefaultName = "QeSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_QE_TABLE_FORMATTER
    tablename_format = SUM_QE_TABLE_FORMATTER
    plotname_format = SUM_QE_PLOT_FORMATTER
