"""Class to collect statistics from analysis of CCD data"""

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.tmpl.file_utils import SLOT_TMPL_TABLE_FORMATTER,\
    RAFT_TMPL_TABLE_FORMATTER, RAFT_TMPL_PLOT_FORMATTER

from lsst.eo_utils.tmpl.meta_analysis import TmplRaftTableAnalysisConfig,\
    TmplRaftTableAnalysisTask


class TemplateConfig(TmplRaftTableAnalysisConfig):
    """Configuration for TempalteTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='tmplsuffix')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class TemplateTask(TmplRaftTableAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = TemplateConfig
    _DefaultName = "TemplateTask"

    intablename_format = SLOT_TMPL_TABLE_FORMATTER
    tablename_format = RAFT_TMPL_TABLE_FORMATTER
    plotname_format = RAFT_TMPL_PLOT_FORMATTER

    datatype = 'tmpl table'

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

        # You should expand this to include space for the data you want to extract
        data_dict = dict(slot=[],
                         amp=[])

        self.log_info_raft_msg(self.config, "")

        for islot, slot in enumerate(ALL_SLOTS):

            self.log_progress("  %s" % slot)

            # get the data from the input table
            #basename = data[slot]
            #datapath = basename.replace(self.config.outsuffix, self.config.insuffix)
            #dtables = TableDict(datapath)

            for amp in range(16):

                # Here you can get the data out for each amp and append it to the
                # data_dict

                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        self.log_progress("Done!")

        outtables = TableDict()
        outtables.make_datatable("tmplsuffix", data_dict)
        return outtables


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
