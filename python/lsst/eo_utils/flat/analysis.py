"""Functions to analyse flat and superbias frames"""


from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from lsst.eo_utils.base.analysis import AnalysisFunc

from .file_utils import get_flat_files_run,\
    slot_flat_tablename, slot_flat_plotname

from .butler_utils import get_flat_files_butler

mpl_utils.set_plt_ioff()


def get_flat_data(butler, run_num, **kwargs):
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

    return retval


class FlatAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis function over all the ccd slots"""

    data_func = get_flat_data

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisBySlot.__init__(self, analysis_func, argnames)


class FlatAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over the rafts """

    data_func = get_flat_data

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisByRaft.__init__(self, analysis_func, argnames)


class FlatAnalysisFunc(AnalysisFunc):
    """Simple functor class to tie together standard flat data analysis
    """

    # These can overridden by the sub-class
    iteratorClass = FlatAnalysisBySlot
    argnames = []
    tablename_func = slot_flat_tablename
    plotname_func = slot_flat_plotname

    def __init__(self, datasuffix=""):
        """ C'tor
        @param datasuffix (str)        Suffix for filenames
        @param kwargs:
        """
        AnalysisFunc.__init__(self, datasuffix)
