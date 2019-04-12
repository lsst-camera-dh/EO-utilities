"""Functions to analyse bias and superbias frames"""

from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisFunc

from .file_utils import get_bias_files_run,\
    slot_bias_tablename, slot_bias_plotname

from .butler_utils import get_bias_files_butler


DEFAULT_BIAS_TYPE = 'spline'
ALL_SLOTS = 'S00 S01 S02 S10 S11 S12 S20 S21 S22'.split()

mpl_utils.set_plt_ioff()

def get_bias_data(butler, run_num, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param butler (`Bulter`)    The data Butler
    @param run_num (str)        The run number we are reading
    @param kwargs:
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    kwargs.pop('run_num', None)
    if butler is None:
        retval = get_bias_files_run(run_num, **kwargs)
    else:
        retval = get_bias_files_butler(butler, run_num, **kwargs)

    return retval


class BiasAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis function over all the ccd slots"""

    data_func = get_bias_data

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisBySlot.__init__(self, analysis_func, argnames)


class BiasAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over the rafts """

    data_func = get_bias_data

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisByRaft.__init__(self, analysis_func, argnames)


class BiasAnalysisFunc(AnalysisFunc):
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    iteratorClass = BiasAnalysisBySlot
    argnames = []
    tablename_func = slot_bias_tablename
    plotname_func = slot_bias_plotname

    def __init__(self, datasuffix=""):
        """ C'tor
        @param datasuffix (str)        Suffix for filenames
        @param kwargs:
        """
        AnalysisFunc.__init__(self, datasuffix)
