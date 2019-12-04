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
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    infilekey = EOUtilOptions.clone_param('infilekey')


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

    datatype = 'lambda table'

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
        return self.get_filename_from_format(PD_CALIB_FORMATTER, '', **kwargs)


class QeRaftTableAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    infilekey = EOUtilOptions.clone_param('infilekey')


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
    datatype = 'lambda table'


class QeSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    dataset = EOUtilOptions.clone_param('dataset')


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

    datatype = 'lambda table'
