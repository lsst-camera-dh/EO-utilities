"""Functions to analyse bias and superbias frames"""

import numpy as np
from scipy import fftpack

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    get_geom_regions, get_raw_image, get_amp_list,\
    get_image_frames_2d, array_struct, unbias_amp

DEFAULT_BIAS_TYPE = 'spline'


def get_biasval_data(butler, ccd, data, **kwargs):
    """Get the bias values and update the data dictionary

    @param butler (Butler)   The data butler
    @param ccd (MaskedCCD)   The ccd we are getting data from
    @param data (dict)       The data we are updating
    @param kwargs:
      slot  (str)       The slot number
      ifile (int)       The file index
      nfiles (int)      Total number of files
      bias_type (str)   Method to use to construct bias
    """
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    ifile = kwargs['ifile']
    nfiles = kwargs['nfiles']

    amps = get_amp_list(butler, ccd)
    for i, amp in enumerate(amps):
        regions = get_geom_regions(butler, ccd, amp)
        serial_oscan = regions['serial_overscan']
        im = get_raw_image(butler, ccd, amp)
        bim = imutil.bias_image(im, serial_oscan, bias_method=bias_type)
        bim_row_mean = bim[serial_oscan].getArray().mean(1)
        key_str = "biasval_%s_a%02i" % (slot, i)
        if key_str not in data:
            data[key_str] = np.ndarray((len(bim_row_mean), nfiles))
        data[key_str][:, ifile] = bim_row_mean


def get_bias_fft_data(butler, ccd, data, **kwargs):
    """Get the fft of the overscan values and update the data dictionary

    @param butler (Butler)   The data butler
    @param ccd (MaskedCCD)   The ccd we are getting data from
    @param data (dict)       The data we are updatign
    @param kwargs:
      slot  (str)                 The slot number
      ifile (int)                 The file index
      nfiles (int)                Total number of files
      bias_type (str)             Method to use to construct bias
      std (str)                   Do standard deviation instead of mean
      superbias_frame (MaskedCCD) The superbias
    """
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    ifile = kwargs.get('ifile', 0)
    nfiles = kwargs.get('nfiles', 1)
    std = kwargs.get('std', False)
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
            struct = array_struct(frames[region], do_std=std)
            fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
            nval = len(fftpow)
            fftpow /= nval/2
            key_str = "fftpow_%s_a%02i" % (slot, i)
            if key_str not in data[key]:
                data[key][key_str] = np.ndarray((int(nval/2), nfiles))
            data[key][key_str][:, ifile] = np.sqrt(fftpow[0:int(nval/2)])


def get_bias_struct_data(butler, ccd, data, **kwargs):
    """Get the bias values and update the data dictionary

    @param butler (Butler)   The data butler
    @param ccd (MaskedCCD)   The ccd we are getting data from
    @param data (dict)       The data we are updating
    @param kwargs:
      slot  (str)                 The slot number
      ifile (int)                 The file index
      nfiles (int)                Total number of files
      bias_type (str)             Method to use to construct bias
      std (bool)                  Used standard deviasion instead of mean
      superbias_frame (MaskedCCD) The superbias
    """
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    ifile = kwargs.get('ifile', 0)
    nfiles = kwargs.get('nfiles', 1)
    std = kwargs.get('std', False)
    superbias_frame = kwargs.get('superbias_frame', None)

    amps = get_amp_list(butler, ccd)
    for i, amp in enumerate(amps):
        regions = get_geom_regions(butler, ccd, amp)
        serial_oscan = regions['serial_overscan']
        im = get_raw_image(butler, ccd, amp)
        if superbias_frame is not None:
            superbias_im = get_raw_image(butler, superbias_frame, amp)
        else:
            superbias_im = None
        image = unbias_amp(im, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
        frames = get_image_frames_2d(image, regions)

        for key, region in zip(REGION_KEYS, REGION_NAMES):
            framekey_row = "row_%s" % key
            framekey_col = "col_%s" % key
            struct = array_struct(frames[region], do_std=std)
            key_str = "biasst_%s_a%02i" % (slot, i)
            if key_str not in data[framekey_row]:
                data[framekey_row][key_str] = np.ndarray((len(struct['rows']), nfiles))
            if key_str not in data[framekey_col]:
                data[framekey_col][key_str] = np.ndarray((len(struct['cols']), nfiles))
            data[framekey_row][key_str][:, ifile] = struct['rows']
            data[framekey_col][key_str][:, ifile] = struct['cols']


def get_correl_wrt_oscan_data(butler, ccd, ref_frames, **kwargs):
    """Get the bias values and update the data dictionary

    @param butler (Butler)   The data butler
    @param ccd (MaskedCCD)   The ccd we are getting data from
    @param data (dict)       The data we are updating
    @param kwargs:
      ifile (int)                 The file index
      s_correl (np.array)         Serial overscan correlations
      p_correl (np.array)         Parallel overscan correlations
    """
    ifile = kwargs['ifile']
    s_correl = kwargs['s_correl']
    p_correl = kwargs['p_correl']
    nrow_i = kwargs['nrow_i']
    ncol_i = kwargs['ncol_i']

    amps = get_amp_list(butler, ccd)
    for i, amp in enumerate(amps):

        regions = get_geom_regions(butler, ccd, amp)
        image = get_raw_image(butler, ccd, amp)
        frames = get_image_frames_2d(image, regions)

        ref_i_array = ref_frames[i]['imaging']
        ref_s_array = ref_frames[i]['serial_overscan']
        ref_p_array = ref_frames[i]['parallel_overscan']

        del_i_array = frames['imaging'] - ref_i_array
        del_s_array = frames['serial_overscan'] - ref_s_array
        del_p_array = frames['parallel_overscan'] - ref_p_array

        dd_s = del_s_array.mean(1)[0:nrow_i]-del_i_array.mean(1)
        dd_p = del_p_array.mean(0)[0:ncol_i]-del_i_array.mean(0)
        mask_s = np.fabs(dd_s) < 50.
        mask_p = np.fabs(dd_p) < 50.

        s_correl[i, ifile-1] = np.corrcoef(del_s_array.mean(1)[0:nrow_i][mask_s],
                                           dd_s[mask_s])[0, 1]
        p_correl[i, ifile-1] = np.corrcoef(del_p_array.mean(0)[0:ncol_i][mask_p],
                                           dd_p[mask_p])[0, 1]


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


def get_serial_oscan_data(butler, ccd, **kwargs):
    """Get the serial overscan data

    @param butler (Butler)   The data butler
    @param ccd (MaskedCCD)   The ccd we are getting data from
    @param kwargs:
      boundry  (int)              Size of buffer around edge of overscan region

    @returns (list) the overscan data
    """
    boundry = kwargs.get('boundry', 10)
    amps = get_amp_list(butler, ccd)
    overscans = []
    for amp in amps:
        regions = get_geom_regions(butler, ccd, amp)
        bbox = regions['serial_overscan']
        im = get_raw_image(butler, ccd, amp)
        bbox.grow(-boundry)
        oscan_data = im[bbox]
        step_x = regions['step_x']
        step_y = regions['step_y']
        overscans.append(oscan_data.getArray()[::step_x, ::step_y])
    return overscans
