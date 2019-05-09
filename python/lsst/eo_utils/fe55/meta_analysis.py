"""Functions to analyse summary data from fe55 analyses"""

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
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class

        It should analyze the input data and create a set of tables
        in a `TableDict` object

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        raise NotImplementedError("Fe55SummaryAnalysisTask.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class

        It should use a `TableDict` object to create a set of
        plots and fill a `FigureDict` object

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        raise NotImplementedError("Fe55SummaryAnalysisTask.plot is not overridden.")
