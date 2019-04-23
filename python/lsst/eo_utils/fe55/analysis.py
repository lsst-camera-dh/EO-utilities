"""Functions to analyse fe55 and superbias frames"""

import sys

from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.fe55.file_utils import get_fe55_files_run,\
    slot_fe55_tablename, slot_fe55_plotname

from lsst.eo_utils.fe55.butler_utils import get_fe55_files_butler

mpl_utils.set_plt_ioff()


def get_fe55_data(caller, butler, run_num, **kwargs):
    """Get a set of fe55 and mask files out of a folder

    @param caller (`Task')     Task we are getting the data for
    @param butler (`Bulter`)    The data Butler
    @param run_num (str)        The run number we are reading
    @param kwargs:
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    kwargs.pop('run_num', None)
    if butler is None:
        retval = get_fe55_files_run(run_num, **kwargs)
    else:
        retval = get_fe55_files_butler(butler, run_num, **kwargs)
    if not retval:
        sys.stdout.write("Warning, call to get_fe55_data for %s returned no data" % caller)

    return retval


class Fe55AnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis function over all the ccd slots"""

    get_data = get_fe55_data

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisBySlot.__init__(self, task)


class Fe55AnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over the rafts """

    get_data = get_fe55_data

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisByRaft.__init__(self, task)


class Fe55AnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilConfig.clone_param('outdir')
    run = EOUtilConfig.clone_param('run')
    raft = EOUtilConfig.clone_param('raft')
    slot = EOUtilConfig.clone_param('slot')
    suffix = EOUtilConfig.clone_param('suffix')
    nfiles = EOUtilConfig.clone_param('nfiles')


class Fe55AnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard fe55 data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = Fe55AnalysisConfig
    _DefaultName = "Fe55AnalysisTask"
    iteratorClass = Fe55AnalysisBySlot

    tablefile_name = slot_fe55_tablename
    plotfile_name = slot_fe55_plotname

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
