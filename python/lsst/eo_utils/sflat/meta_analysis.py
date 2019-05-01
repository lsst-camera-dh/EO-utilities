"""Functions to analyse summary data from bias and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.sflat.file_utils import SUM_SFLAT_TABLE_FORMATTER,\
    SUM_SFLAT_PLOT_FORMATTER, RAFT_SFLAT_TABLE_FORMATTER


class SflatSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class SflatSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard sflat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SflatSummaryAnalysisConfig
    _DefaultName = "SflatSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_SFLAT_TABLE_FORMATTER
    tablename_format = SUM_SFLAT_TABLE_FORMATTER
    plotname_format = SUM_SFLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """ C'tor
        @param kwargs:
        """
        AnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
