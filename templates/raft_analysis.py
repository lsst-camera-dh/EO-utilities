"""Class to analyze data for all ccds on a raft"""

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.iter_utils import AnalysisByRaft

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.tmpl.file_utils import RAFT_TMPL_TABLE_FORMATTER, RAFT_TMPL_PLOT_FORMATTER

from lsst.eo_utils.tmpl.analysis import TmplAnalysisTask, TmplAnalysisConfig



class TemplateConfig(TmplAnalysisConfig):
    """Configuration for TemplateTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class TemplateTask(TmplAnalysisTask):
    """Analyze some tmpl data"""

    ConfigClass = TemplateConfig
    _DefaultName = "TemplateTask"
    iteratorClass = AnalysisByRaft

    tablename_format = RAFT_TMPL_TABLE_FORMATTER
    plotname_format = RAFT_TMPL_PLOT_FORMATTER

    datatype = 'tmpl'

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        TmplAnalysisTask.__init__(self, **kwargs)

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
            output data tables
        """
        self.safe_update(**kwargs)

        slots = ALL_SLOTS

        # This is a dictionary of dictionaries to store all the
        # data you extract from the tmpl_files
        data_dict = {}

        for slot in slots:

            #Get the datafiles, and the correpsonding superbias files
            tmpl_files = data[slot]['TMPL']
            print(tmpl_files)

            #mask_files = self.get_mask_files(slot=slot)
            #superbias_frame = self.get_superbias_frame(mask_files, slot=slot)

            # Analysis goes here, you should fill data_dict with data extracted
            # by the analysis
            #

        dtables = TableDict()
        for key, val in data_dict.items():
            dtables.make_datatable(key, val)

        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Make plots

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
