"""Functions to analyse bias and superbias frames"""

import numpy as np

from lsst.eo_utils.base.defaults import DEFAULT_BIAS_TYPE

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    get_geom_regions, get_raw_image, get_amp_list,\
    get_image_frames_2d, array_struct, unbias_amp


def stack_by_amps(stack_arrays, butler, ccd, **kwargs):
    """Stack arrays for all the amps to look for coherent noise

    Parameters
    ----------
    stack_arrays : `dict`
        Dictionary of arrays with stacked data, filled by this function
    butler : `Butler` or `None`
        The data butler
    ccd : `MaskedCCD`
        The ccd we are getting data from

    Keywords
    --------
    ifile : `int`
        File index
    bias_type : `str`
        Method to use to construct bias
    superbias_frame : `MaskedCCD` or `None`
        The superbias frame to subtract off
    """
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    ifile = kwargs['ifile']
    superbias_frame = kwargs.get('superbias_frame', None)

    amps = get_amp_list(butler, ccd)
    for i, amp in enumerate(amps):

        regions = get_geom_regions(butler, ccd, amp)
        serial_oscan = regions['serial_overscan']
        img = get_raw_image(butler, ccd, amp)
        if superbias_frame is not None:
            if butler is not None:
                superbias_im = get_raw_image(None, superbias_frame, amp+1)
            else:
                superbias_im = get_raw_image(None, superbias_frame, amp)
        else:
            superbias_im = None
        image = unbias_amp(img, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
        frames = get_image_frames_2d(image, regions)

        for key, region in zip(REGION_KEYS, REGION_NAMES):
            row_stack = stack_arrays["row_%s" % key]
            col_stack = stack_arrays["col_%s" % key]
            struct = array_struct(frames[region])
            row_stack[ifile, i] = struct['rows']
            col_stack[ifile, i] = struct['cols']



def convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles):
    """Convert the stack arrays to a dictionary

    Parameters
    ----------
    stack_arrays : `dict`
        The stacked data
    dim_array_dict : `dict`
        The array shapes
    nfiles : `int`
        Number of input files

    Returns
    -------
    stackdata_dict : `dict`
        The re-organized data
    """
    stackdata_dict = {}

    for key, xvals in dim_array_dict.items():
        stack = stack_arrays[key]
        amp_mean = stack.mean(0).mean(1)
        stackdata_dict[key] = {key:xvals}

        for i in range(nfiles):
            amp_stack = (stack[i].T - amp_mean).T
            mean_val = amp_stack.mean(0)
            std_val = amp_stack.std(0)
            signif_val = mean_val / std_val
            for stat, val in zip(['mean', 'std', 'signif'], [mean_val, std_val, signif_val]):
                keystr = "stack_%s" % stat
                if keystr not in stackdata_dict[key]:
                    stackdata_dict[key][keystr] = np.ndarray((len(val), nfiles))
                stackdata_dict[key][keystr][:, i] = val
    return stackdata_dict
