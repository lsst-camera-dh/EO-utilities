"""Functions to analyse summary data from bias and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.fe55.file_utils import RAFT_FE55_TABLE_FORMATTER,\
    SUM_FE55_TABLE_FORMATTER, SUM_FE55_PLOT_FORMATTER



class Fe55SummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class Fe55SummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard fe55 data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = Fe55SummaryAnalysisConfig
    _DefaultName = "Fe55SummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator
    argnames = ['dataset', 'butler_repo']

    intablename_format = RAFT_FE55_TABLE_FORMATTER
    tablename_format = SUM_FE55_TABLE_FORMATTER
    plotname_format = SUM_FE55_PLOT_FORMATTER

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
