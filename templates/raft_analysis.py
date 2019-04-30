"""Class to analyze the correlations between the overscans for all amplifiers on a raft"""

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.iter_utils import AnalysisByRaft

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.tmpl.file_utils import RAFT_TMPL_TABLE_FORMATTER, RAFT_TMPL_PLOT_FORMATTER

from lsst.eo_utils.tmpl.analysis import TmplAnalysisTask, TmplAnalysisConfig



class TmplTemplateConfig(TmplAnalysisConfig):
    """Configuration for TmplTemplateTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='tmplsuffix')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class TmplTemplateTask(TmplAnalysisTask):
    """Analyze the correlations between the overscans for all amplifiers on a raft"""

    ConfigClass = TmplTemplateConfig
    _DefaultName = "TmplTemplateTask"
    iteratorClass = AnalysisByRaft

    tablename_format = RAFT_TMPL_TABLE_FORMATTER
    plotname_format = RAFT_TMPL_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor"""
        TmplAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the tmpl and mask files
        @param kwargs            Used to override configuration

        @returns (TableDict)
        """
        self.safe_update(**kwargs)

        slots = ALL_SLOTS

        # This is a dictionary of dictionaries to store all the
        # data you extract from the tmpl_files
        data_dict = {}

        for slot in slots:
            tmpl_files = data[slot]['TMPL']

            mask_files = self.get_mask_files(slot=slot)
            superbias_frame = self.get_superbias_frame(mask_files, slot=slot)

            # Analysis goes here, you should fill data_dict with data extracted
            # by the analysis
            #


        dtables = TableDict()
        for key, val in data_dict.items():
            dtables.make_datatable(key, val)

        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Plot the tmpl fft

        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
        """
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


EO_TASK_FACTORY.add_task_class('TmplTemplate', TmplTemplateTask)
