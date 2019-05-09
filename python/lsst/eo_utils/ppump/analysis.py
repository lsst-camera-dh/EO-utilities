"""Functions to analyse ppump and superbias frames"""

import sys

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.ppump.file_utils import get_ppump_files_run,\
    SLOT_PPUMP_TABLE_FORMATTER, SLOT_PPUMP_PLOT_FORMATTER

from lsst.eo_utils.ppump.butler_utils import get_ppump_files_butler


class PpumpAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')
    nfiles = EOUtilOptions.clone_param('nfiles')


class PpumpAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard ppump data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = PpumpAnalysisConfig
    _DefaultName = "PpumpAnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_PPUMP_TABLE_FORMATTER
    plotname_format = SLOT_PPUMP_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)

    def get_data(self, butler, run_num, **kwargs):
        """Get a set of ppump and mask files out of a folder

        @param butler (`Bulter`)    The data Butler
        @param run_num (str)        The run number we are reading
        @param kwargs:
           acq_types (list)  The types of acquistions we want to include

        @returns (dict) Dictionary mapping slot to file names
        """
        kwargs.pop('run_num', None)

        if butler is None:
            retval = get_ppump_files_run(run_num, **kwargs)
        else:
            retval = get_ppump_files_butler(butler, run_num, **kwargs)
        if not retval:
            sys.stdout.write("Warning, call to get_data for %s returned no data" % self.getName())
        return retval

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
