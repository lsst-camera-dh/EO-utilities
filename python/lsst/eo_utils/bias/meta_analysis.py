"""Functions to analyse summary data from bias and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import SummaryAnalysisIterator

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import SUM_BIAS_TABLE_FORMATTER, SUM_BIAS_PLOT_FORMATTER,\
    SUM_SBIAS_TABLE_FORMATTER, SUM_SBIAS_PLOT_FORMATTER,\
    RAFT_BIAS_TABLE_FORMATTER, RAFT_SBIAS_TABLE_FORMATTER



class BiasSummaryAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


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
        raise NotImplementedError("BiasSummaryAnalysisTask.extract is not overridden.")

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
        raise NotImplementedError("BiasSummaryAnalysisTask.plot is not overridden.")


class SuperbiasSummaryAnalysisConfig(AnalysisConfig):
    """Configuration for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class SuperbiasSummaryAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SuperbiasSummaryAnalysisConfig
    _DefaultName = "BiasSummaryAnalysisTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = RAFT_SBIAS_TABLE_FORMATTER
    tablename_format = SUM_SBIAS_TABLE_FORMATTER
    plotname_format = SUM_SBIAS_PLOT_FORMATTER

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
        raise NotImplementedError("SuperbiasSummaryAnalysisTask.extract is not overridden.")

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
        raise NotImplementedError("SuperbiasSummaryAnalysisTask.plot is not overridden.")
