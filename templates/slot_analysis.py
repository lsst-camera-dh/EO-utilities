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


class TmplTemplateConfig(TmplAnalysisConfig):
    """Configuration for TmplTemplateTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class TmplSlotTemplatetTask(TmplAnalysisTask):
    """Analyze some tmpl data"""

    ConfigClass = TmplSlotTemplateConfig
    _DefaultName = "TmplSlotTemplate"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor """
        TmplAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the data

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the tmpl and mask files
        @param kwargs              Used to override defaults

        @returns (TableDict) with the extracted data
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
        """Plot the data

        @param dtables (`TableDict`)  The data
        @param figs (`FigureDict`)    Object to store the figues
        """
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


class TmplSlotTemplateStatsConfig(TmplAnalysisConfig):
    """Configuration for TmplSlotTempalteStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='tmplsuffix')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class TmplSlotTemplateStatsTask(TmplAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = TmplSlotTemplateStatsConfig
    _DefaultName = "TmplSlotTemplateStats"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_TMPL_TABLE_FORMATTER
    tablename_format = RAFT_TMPL_TABLE_FORMATTER
    plotname_format = RAFT_TMPL_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor """
        TmplAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract the data

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the tmpl and mask files
        @param kwargs              Used to override defaults

        @returns (TableDict) with the extracted data
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
        """Plot the summary data from the tmpl fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs




EO_TASK_FACTORY.add_task_class('TmplSlotTemplate', TmplSlotTemplateTask)
EO_TASK_FACTORY.add_task_class('TmplSlotTemplateStats', TmplSlotTemplateStatsTask)