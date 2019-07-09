"""Class to analyze the FFT of the bias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.tmpl.meta_analysis import TmplSummaryAnalysisConfig, TmplSummaryAnalysisTask


class TemplateConfig(TmplSummaryAnalysisConfig):
    """Configuration for TemplateTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='tmplsuffix_stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class TemplateTask(TmplSummaryAnalysisTask):
    """Summarize the analysis results for many runs"""

    ConfigClass = TemplateConfig
    _DefaultName = "TemplateTask"

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        TmplSummaryAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract data

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
            Output data tables
        """
        self.safe_update(**kwargs)

        for key, val in data.items():
            data[key] = val.replace(self.config.outsuffix, self.config.insuffix)

        # Define the set of columns to keep and remove
        # keep_cols = []
        # remove_cols = []

        outtable = vstack_tables(data, tablename='tmplsuffix_stats')

        dtables = TableDict()
        dtables.add_datatable('tmplsuffix_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


EO_TASK_FACTORY.add_task_class('Template', TemplateTask)
