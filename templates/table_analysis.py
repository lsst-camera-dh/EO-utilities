"""Class to analyze the FFT of the bias frames"""

import sys

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.tmpl.file_utils import SLOT_TMPL_TABLE_FORMATTER,\
    RAFT_TMPL_TABLE_FORMATTER, RAFT_TMPL_PLOT_FORMATTER

from lsst.eo_utils.tmpl.analysis import TmplAnalysisConfig, TmplAnalysisTask


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
    iteratorClass = TableAnalysisBySlot

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
            Output data tables
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        tmpl_files = data['TMPL']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(tmpl_files)))
        sys.stdout.flush()

        # This is a dictionary of dictionaries to store all the
        # data you extract from the tmpl_files
        data_dict = {}

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #

        sys.stdout.write("!\n")
        sys.stdout.flush()

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


class TemplateStatsConfig(TmplAnalysisConfig):
    """Configuration for TempalteStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='tmplsuffix')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class TemplateStatsTask(TmplAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = TemplateStatsConfig
    _DefaultName = "TemplateStatsTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_TMPL_TABLE_FORMATTER
    tablename_format = RAFT_TMPL_TABLE_FORMATTER
    plotname_format = RAFT_TMPL_PLOT_FORMATTER

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
            Output data tables
        """
        self.safe_update(**kwargs)

        # You should expand this to include space for the data you want to extract
        data_dict = dict(slot=[],
                         amp=[])

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace(self.config.outsuffix, self.config.insuffix)

            dtables = TableDict(datapath)

            for amp in range(16):

                # Here you can get the data out for each amp and append it to the
                # data_dict

                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        sys.stdout.write(".\n")
        sys.stdout.flush()

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
EO_TASK_FACTORY.add_task_class('TemplateStats', TemplateStatsTask)
