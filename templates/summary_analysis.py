"""Class to analyze the FFT of the bias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.tmpl.meta_analysis import TmplSummaryAnalysisConfig, TmplSummaryAnalysisTask


class TmplSummaryTemplateConfig(TmplSummaryAnalysisConfig):
    """Configuration for TmplSummaryTemplateTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='tmplsuffix_stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class TmplSummaryTemplateTask(TmplSummaryAnalysisTask):
    """Summarize the analysis results for many runs"""

    ConfigClass = TmplSummaryTemplateConfig
    _DefaultName = "TmplSummaryTemplateTask"

    def __init__(self, **kwargs):
        """C'tor"""
        TmplSummaryAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the data

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the tmpl and mask files
        @param kwargs              Used to override defaults

        @returns (TableDict)
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
        """Plot the summary data from the superbias statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


EO_TASK_FACTORY.add_task_class('TmplSummaryTemplate', TmplSummaryTemplateTask)
