"""Class to analyze individual CCD data"""


from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.tmpl.meta_analysis import TmplSlotTableAnalysisConfig,\
    TmplSlotTableAnalysisTask


class TemplateConfig(TmplSlotTableAnalysisConfig):
    """Configuration for TemplateTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class TemplateTask(TmplSlotTableAnalysisTask):
    """Analyze some tmpl data"""

    ConfigClass = TemplateConfig
    _DefaultName = "TemplateTask"

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

        # Get the slot, if needed
        #slot = self.config.slot
        tmpl_files = data

        # Get the superbias frame, if needed
        #mask_files = self.get_mask_files()
        #superbias_frame = self.get_superbias_frame(mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(tmpl_files))

        # This is a dictionary of dictionaries to store all the
        # data you extract from the tmpl_files
        data_dict = {}

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, tmpl_files))
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
