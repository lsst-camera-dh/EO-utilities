"""Functions to analyse bias and superbias frames"""


from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import get_bias_files_run,\
    slot_bias_tablename, slot_bias_plotname

from .butler_utils import get_bias_files_butler

mpl_utils.set_plt_ioff()


def get_bias_data(caller, butler, run_num, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param caller (`Task')     Task we are getting the data for
    @param butler (`Bulter`)    The data Butler
    @param run_num (str)        The run number we are reading
    @param kwargs:
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    kwargs.pop('run', None)
    if butler is None:
        retval = get_bias_files_run(run_num, **kwargs)
    else:
        retval = get_bias_files_butler(butler, run_num, **kwargs)
    if len(retval) == 0:
        sys.stdout.write("Warning, call to get_bias_data for %s returned no data" % caller)
    return retval


class BiasAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis function over all the ccd slots"""

    # Function to get the data
    get_data = get_bias_data

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisBySlot.__init__(self, task)


class BiasAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over the rafts """

    # Function to get the data
    get_data = get_bias_data

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisByRaft.__init__(self, task)


class BiasAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilConfig.clone_param('outdir')
    run = EOUtilConfig.clone_param('run')
    raft = EOUtilConfig.clone_param('raft')
    slot = EOUtilConfig.clone_param('slot')
    suffix = EOUtilConfig.clone_param('suffix')
    nfiles = EOUtilConfig.clone_param('nfiles')


class BiasAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """
    # These can overridden by the sub-class
    ConfigClass = BiasAnalysisConfig
    _DefaultName = "BiasAnalysis"
    iteratorClass = BiasAnalysisBySlot

    tablefile_name = slot_bias_tablename
    plotfile_name = slot_bias_plotname

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        super(BiasAnalysisTask, self).__init__(**kwargs)
