"""Utilities for offline data analysis of LSST Electrical-Optical testing"""


from lsst.eotest.sensor import add_mask_files


from .iter_utils import AnalysisBySlot
from .file_utils import makedir_safe, get_mask_files_run, mask_filename



def get_mask_data(butler, run_num, **kwargs):
    """Get a set of mask files out of a folder

    @param: butler (Bulter)  The data Butler
    @param run_num (str)     The number number we are reading
    @param kwargs:
        mask_types (list)       The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    kwargs.pop('run_num', None)
    if butler is None:
        retval = get_mask_files_run(run_num, **kwargs)
    else:
        raise NotImplementedError("Can't get mask files from Butler")

    return retval


def make_mask(butler, slot_data, **kwargs):
    """Make a mask file by or-ing together a set of other mask files

    @param: butler (Bulter)  The data Butler
    @param slot_data (dict)  Dictionary pointing to the mask files
    @param kwargs:           Passed to the `mask_filename` function to get the
                             output filename
    """
    mask_files = slot_data['MASK']
    if butler is not None:
        print("Ignoring Butler to get mask files")
    outfile = mask_filename(**kwargs)
    makedir_safe(outfile)
    add_mask_files(mask_files, outfile)


class MaskAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis task over all the slots in a raft"""

    data_func = get_mask_data

    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments needed by that function,
                                        used to look up defaults
        """
        super(MaskAnalysisBySlot, self).__init__(analysis_func, argnames)
