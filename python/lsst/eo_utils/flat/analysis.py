"""Functions to analyse flat and superbias frames"""


from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.flat.file_utils import get_flat_files_run,\
    slot_flat_tablename, slot_flat_plotname

from lsst.eo_utils.flat.butler_utils import get_flat_files_butler

mpl_utils.set_plt_ioff()


def get_flat_data(caller, butler, run_num, **kwargs):
    """Get a set of flat and mask files out of a folder

    @param butler (`Bulter`)    The data Butler
    @param run_num (str)        The run number we are reading
    @param kwargs:
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    kwargs.pop('run_num', None)
    if butler is None:
        retval = get_flat_files_run(run_num, **kwargs)
    else:
        retval = get_flat_files_butler(butler, run_num, **kwargs)
    if not retval:
        sys.stdout.write("Warning, call to get_flat_data for %s returned no data" % caller)

    return retval


class FlatAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis function over all the ccd slots"""

    get_data = get_flat_data

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisBySlot.__init__(self, task)


class FlatAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over the rafts """

    get_data = get_flat_data

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisByRaft.__init__(self, task)


class FlatAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilConfig.clone_param('outdir')
    run = EOUtilConfig.clone_param('run')
    raft = EOUtilConfig.clone_param('raft')
    slot = EOUtilConfig.clone_param('slot')
    suffix = EOUtilConfig.clone_param('suffix')
    nfiles = EOUtilConfig.clone_param('nfiles')


class FlatAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard flat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = FlatAnalysisConfig
    _DefaultName = "FlatAnalysisTask"
    iteratorClass = FlatAnalysisBySlot

    tablefile_name = slot_flat_tablename
    plotfile_name = slot_flat_plotname

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
