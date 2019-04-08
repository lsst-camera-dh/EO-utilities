"""Functions to analyse bias and superbias frames"""

import numpy as np
from scipy import fftpack

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    get_geom_regions, get_raw_image, get_amp_list,\
    get_image_frames_2d, array_struct, unbias_amp

DEFAULT_BIAS_TYPE = 'spline'



def stack_by_amps(stack_arrays, butler, ccd, **kwargs):
    """Stack arrays for all the amps to look for coherent noise

    @param stack_arrays (dict) Dictionary of arrays with stacked data
    @param butler (Butler)     The data butler
    @param ccd (MaskedCCD)     The ccd we are getting data from
    @param kwargs:
      ifile (int)                 File index
      bias_type (str)             Method to use to construct bias
      superbias_frame (MaskedCCD) The superbias
    """
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    ifile = kwargs['ifile']
    superbias_frame = kwargs.get('superbias_frame', None)

    amps = get_amp_list(butler, ccd)
    for i, amp in enumerate(amps):

        regions = get_geom_regions(butler, ccd, amp)
        serial_oscan = regions['serial_overscan']
        im = get_raw_image(butler, ccd, amp)
        if superbias_frame is not None:
            if butler is not None:
                superbias_im = get_raw_image(None, superbias_frame, amp+1)
            else:
                superbias_im = get_raw_image(None, superbias_frame, amp)
        else:
            superbias_im = None
        image = unbias_amp(im, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
        frames = get_image_frames_2d(image, regions)

        for key, region in zip(REGION_KEYS, REGION_NAMES):
            row_stack = stack_arrays["row_%s" % key]
            col_stack = stack_arrays["col_%s" % key]
            struct = array_struct(frames[region])
            row_stack[ifile, i] = struct['rows']
            col_stack[ifile, i] = struct['cols']



def convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles):
    """Convert the stack arrays to a dictionary

    @param stack_arrays (dict)   The stacked data
    @param dim_array_dict (dict) The array shapes
    @param nfiles (int)          Number of input files

    @returns (dict) the re-organized data
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


def get_serial_oscan_data(butler, ccd, **kwargs):
    """Get the serial overscan data

    @param butler (Butler)   The data butler
    @param ccd (MaskedCCD)   The ccd we are getting data from
    @param kwargs:
      boundry  (int)              Size of buffer around edge of overscan region
      bias_type (str)             Method to use to construct bias
      superbias_frame (MaskedCCD) The superbias

    @returns (list) the overscan data
    """
    boundry = kwargs.get('boundry', 10)
    amps = get_amp_list(butler, ccd)
    superbias_frame = kwargs.get('superbias_frame', None)
    overscans = []
    for amp in amps:
        if superbias_frame is not None:
            if butler is not None:
                superbias_im = get_raw_image(None, superbias_frame, amp+1)
            else:
                superbias_im = get_raw_image(None, superbias_frame, amp)
        else:
            superbias_im = None

        regions = get_geom_regions(butler, ccd, amp)
        serial_oscan = regions['serial_overscan']
        im = get_raw_image(butler, ccd, amp)
        image = unbias_amp(im, serial_oscan, bias_type=None, superbias_im=superbias_im)
        serial_oscan.grow(-boundry)
        oscan_data = image[serial_oscan]
        step_x = regions['step_x']
        step_y = regions['step_y']
        overscans.append(oscan_data.getArray()[::step_x, ::step_y])
    return overscans


def get_superbias_stats(butler, superbias, stats_data, **kwargs):
    """Get the serial overscan data

    @param butler (Butler)         The data butler
    @param superbias (MaskedCCD)   The ccd we are getting data from
    @param stats_data (dict)       The dictionary we are filling
    @param kwargs:
      islot (int)              Index of the slot in question
    """
    amps = get_amp_list(butler, superbias)
    islot = kwargs.get('islot')

    if 'mean' not in stats_data:
        stats_data['mean'] = np.ndarray((9, 16))
        stats_data['median'] = np.ndarray((9, 16))
        stats_data['std'] = np.ndarray((9, 16))
        stats_data['min'] = np.ndarray((9, 16))
        stats_data['max'] = np.ndarray((9, 16))

    for i, amp in enumerate(amps):
        im = get_raw_image(butler, superbias, amp)
        stats_data['mean'][islot, i] = im.array.mean()
        stats_data['median'][islot, i] = np.median(im.array)
        stats_data['std'][islot, i] = im.array.std()
        stats_data['min'][islot, i] = im.array.min()
        stats_data['max'][islot, i] = im.array.max()
