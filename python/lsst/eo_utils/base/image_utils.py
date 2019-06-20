"""This module contains functions to get particular bits of data out of images.
These functions will work both with Butlerized and un-Butlerized data.

"""

import numpy as np

from scipy import fftpack

from astropy.io import fits

import lsst.afw.math as afwMath
import lsst.afw.image as afwImage

import lsst.eotest.image_utils as imutil
from lsst.eotest.sensor import MaskedCCD

from .defaults import T_SERIAL, T_PARALLEL

# These are the names and labels for the parts of the data array
REGION_KEYS = ['i', 's', 'p']
REGION_NAMES = ['imaging', 'serial_overscan', 'parallel_overscan']
REGION_LABELS = ['Imaging region', 'Serial overscan', 'Parallel overscan']

try:
    AFWIMAGE_MASK = afwImage.MaskU
except AttributeError:
    AFWIMAGE_MASK = afwImage.Mask


def get_dims_from_ccd(butler, ccd):
    """Get the CCD amp dimensions for a particular dataId or file

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    odict : `dict`
        Dictionary with the dimensions
    """
    if butler is None:
        geom = ccd.amp_geom
        o_dict = dict(nrow_i=geom.imaging.getHeight(),
                      nrow_s=geom.serial_overscan.getHeight(),
                      nrow_p=geom.parallel_overscan.getHeight(),
                      ncol_i=geom.imaging.getWidth(),
                      ncol_s=geom.serial_overscan.getWidth(),
                      ncol_p=geom.parallel_overscan.getWidth(),
                      ncol_f=geom.naxis1)
    else:
        geom = ccd.getDetector()[0]
        o_dict = dict(nrow_i=geom.getBBox().getHeight(),
                      nrow_s=geom.getRawHorizontalOverscanBBox().getHeight(),
                      nrow_p=geom.getRawVerticalOverscanBBox().getHeight(),
                      ncol_i=geom.getBBox().getWidth(),
                      ncol_s=geom.getRawHorizontalOverscanBBox().getWidth(),
                      ncol_p=geom.getRawVerticalOverscanBBox().getWidth(),
                      ncol_f=geom.getRawBBox().getWidth())
    return o_dict


def get_readout_freqs_from_ccd(butler, ccd):
    """Get the frequencies corresponding to the FFTs

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    odict : `dict`
        Dictionary with the frequencies
    """

    if butler is None:
        geom = ccd.amp_geom
        nrow_i = geom.imaging.getHeight()
        nrow_s = geom.serial_overscan.getHeight()
        nrow_p = geom.parallel_overscan.getHeight()
        ncol_f = geom.naxis1
    else:
        geom = ccd.getDetector()[0]
        nrow_i = geom.getBBox().getHeight()
        nrow_s = geom.getRawHorizontalOverscanBBox().getHeight()
        nrow_p = geom.getRawVerticalOverscanBBox().getHeight()
        ncol_f = geom.getRawBBox().getWidth()

    t_row = ncol_f*T_SERIAL + T_PARALLEL
    f_s = 1./t_row

    o_dict = dict(freqs_i=fftpack.fftfreq(nrow_i)*f_s,
                  freqs_s=fftpack.fftfreq(nrow_s)*f_s,
                  freqs_p=fftpack.fftfreq(nrow_p)*f_s)
    return o_dict


def get_geom_steps_manu_hdu(manu, amp):
    """Get x and y steps (+1 or -1) to convert between
    readout and physical orientation for a particular amp

    Parameters
    ----------
    manu : `str`
        Manufactor 'ITL' or 'E2V'
    amp : `int`
        HDU index

    Returns
    -------
    step_x : `int`
        Step to take in x to go from readout to physical order
    step_y : `int`
        Step to take in y to go from readout to physical order
    """
    if manu == 'ITL':
        flip_y = -1
    elif manu == 'E2V':
        flip_y = 1
    else:
        raise ValueError("Unknown CCD type %s" % manu)

    if amp <= 8:
        step_x = 1
        step_y = -1
    else:
        step_x = -1
        step_y = flip_y
    return (step_x, step_y)


def get_geom_steps_from_amp(ccd, amp):
    """Get x and y steps (+1 or -1) to convert between
    readout and physical orientation for a particular amp

    Parameters
    ----------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object
    amp : `int`
        Amplifier index

    Returns
    -------
    step_x : `int`
        Step to take in x to go from readout to physical order
    step_y : `int`
        Step to take in y to go from readout to physical order
    """
    manu = ccd.getInfo().getMetadata().getString('CCD_MANU')
    if manu == 'ITL':
        flip_y = -1
    elif manu == 'E2V':
        flip_y = 1
    else:
        raise ValueError("Unknown CCD type %s" % manu)

    if amp < 8:
        step_x = 1
        step_y = -1
    else:
        step_x = -1
        step_y = flip_y
    return (step_x, step_y)


def flip_data_in_place(filepath):
    """Flip the data in a FITS file in place

    Parameters
    ----------
    filepath : `str`
        The file we are adjusting
    """
    hdus = fits.open(filepath)
    manu = hdus[0].header['CCD_MANU']
    for amp in range(1, 17):
        (step_x, step_y) = get_geom_steps_manu_hdu(manu, amp)
        hdus[amp].data = hdus[amp].data[::step_x, ::step_y]
    hdus.writeto(filepath, overwrite=True)


def get_geom_regions(butler, ccd, amp):
    """Get the ccd amp bounding boxes for a particular dataId or file

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object
    amp : `int`
        Amplifier index

    Returns
    -------
    odict : `dict`
        Dictionary with the bounding boxes
    """
    if butler is None:
        geom = ccd.amp_geom
        o_dict = dict(imaging=geom.imaging,
                      serial_overscan=geom.serial_overscan,
                      parallel_overscan=geom.parallel_overscan,
                      prescan=geom.prescan,
                      offset=None,
                      step_x=1,
                      step_y=1)
    else:
        geom = ccd.getDetector()[amp]
        step_x, step_y = get_geom_steps_from_amp(ccd, amp)
        o_dict = dict(imaging=geom.getRawDataBBox(),
                      serial_overscan=geom.getRawHorizontalOverscanBBox(),
                      parallel_overscan=geom.getRawVerticalOverscanBBox(),
                      prescan=geom.getRawPrescanBBox(),
                      offset=geom.getRawXYOffset(),
                      step_x=step_x,
                      step_y=step_y)
    return o_dict


def get_dimension_arrays_from_ccd(butler, ccd):
    """Get the linear arrays with the indices for each direction and readout region

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    odict : `dict`
        Dictionary with the arrays
    """

    if butler is None:
        geom = ccd.amp_geom
        nrow_i = geom.imaging.getHeight()
        nrow_s = geom.serial_overscan.getHeight()
        nrow_p = geom.parallel_overscan.getHeight()
        ncol_i = geom.imaging.getWidth()
        ncol_s = geom.serial_overscan.getWidth()
        ncol_p = geom.parallel_overscan.getWidth()
    else:
        geom = ccd.getDetector()[0]
        nrow_i = geom.getBBox().getHeight()
        nrow_s = geom.getRawHorizontalOverscanBBox().getHeight()
        nrow_p = geom.getRawVerticalOverscanBBox().getHeight()
        ncol_i = geom.getBBox().getWidth()
        ncol_s = geom.getRawHorizontalOverscanBBox().getWidth()
        ncol_p = geom.getRawVerticalOverscanBBox().getWidth()

    o_dict = {'row_i':np.linspace(0, nrow_i-1, nrow_i),
              'row_s':np.linspace(0, nrow_s-1, nrow_s),
              'row_p':np.linspace(0, nrow_p-1, nrow_p),
              'col_i':np.linspace(0, ncol_i-1, ncol_i),
              'col_s':np.linspace(0, ncol_s-1, ncol_s),
              'col_p':np.linspace(0, ncol_p-1, ncol_p)}
    return o_dict


def get_raw_image(butler, ccd, amp):
    """Get the raw image for a particular amp

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object
    amp : `int`
        Amplifier index

    Returns
    -------
    odict : `ImageF`
        The image
    """
    if butler is None:
        img = ccd[amp].getImage()
    else:
        geom = ccd.getDetector()
        img = ccd.maskedImage[geom[amp].getRawBBox()].image
    return img


def get_ccd_from_id(butler, data_id, mask_files, bias_frame=None):
    """Get a CCD image from a data_id

    If we are using `Butler` then this will take a
    data_id `dict` ojbect and return an `ExposureF` object

    If we are not using `Butler` (i.e., if bulter is `None`)
    then this will take a filename and return a `MaskedCCD` object

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    data_id : `dict` or `str`
        Data identier
    mask_files : `list`
        List of data_ids for the files to construct the pixel mask
    bias_frame : `ExposureF` or `MaskedCCD` or `None`
        Object with the bias data

    Returns
    -------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object
    """
    if butler is None:
        exposure = MaskedCCD(str(data_id),
                             mask_files=mask_files,
                             bias_frame=bias_frame)
    else:
        exposure = butler.get('raw', data_id)
        apply_masks(butler, exposure, mask_files)
    return exposure


def get_amp_list(butler, ccd):
    """Get the Geometry for a particular dataId or file

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    amplist : `list`
        List of amplifier indices
    """
    if butler is None:
        amplist = [amp for amp in ccd]
    else:
        amplist = [amp for amp in range(16)]
    return amplist


def get_image_frames_2d(img, regions, regionlist=None):
    """Split out the arrays for the serial_overscan, parallel_overscan, and imaging regions

    Parameters
    ----------
    img : `ImageF`
        Image Data
    regions : `dict`
        Bounding boxes for the regions
    regionlist : `list` or `None`
        Names of the regions to extract data for

    Returns
    -------
    o_dict : `dict`
        Dictionary mapping name to data array for each region
    """
    step_x = regions['step_x']
    step_y = regions['step_y']

    if regionlist is None:
        regionlist = ['imaging', 'serial_overscan', 'parallel_overscan']

    try:
        o_dict = {key:img[regions[key]].getArray()[::step_x, ::step_y] for key in regionlist}
    except AttributeError:
        o_dict = {key:img[regions[key]].getImage().getArray()[::step_x, ::step_y]
                  for key in regionlist}
    return o_dict


def get_data_as_read(butler, ccd, amp, regionlist=None):
    """Split out the arrays for the serial_overscan, parallel_overscan, and imaging regions
    and return the data in the readout order.

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler (or none)
    ccd : `ImageF` or `MaskedImageF`
        CCD image object
    amp : `int`
        Amplifier index
    regionlist : `list` or `None`
        List of regions

    Returns
    -------
    o_dict : `dict`
        Dictionary mapping name to data array for each region
    """
    raw_image = get_raw_image(butler, ccd, amp)
    regions = get_geom_regions(butler, ccd, amp)
    frames = get_image_frames_2d(raw_image, regions, regionlist)
    return frames


def array_struct(i_array, clip=None, do_std=False):
    """Extract the row-by-row and col-by-col mean (or standard deviation)

    Parameters
    ----------
    i_array : `array`
        The input data
    clip : `tuple`
        min and max used to clip the data, None implies no clipping
    do_std : `bool`
        If true return the standard deviation instead of the mean

    Returns
    -------
    o_dict : `dict`
       Dictionary with
       rows : `array`  Row-wise means (or standard deviations)
       cols : `array`  Col-wise means (or standard deviations)
    """

    if clip is not None:
        clipped_array = i_array.clip(clip)
    else:
        clipped_array = i_array

    if do_std:
        rows = clipped_array.std(1)
        cols = clipped_array.std(0)
    else:
        rows = clipped_array.mean(1)
        cols = clipped_array.mean(0)

    o_dict = dict(rows=rows,
                  cols=cols)
    return o_dict


def unbias_amp(img, serial_oscan, bias_type=None, superbias_im=None, region=None):
    """Unbias the data from a particular amp

    Paramters
    ---------
    img : `ImageF`
        The image
    serial_oscan : `Box2I`
        Serial overscan bounding box
    bias_type : `str` or `None`
        Method of unbiasing to applly
    superbias_im : `ImageF`
        Optional superbias frame to subtract off
    region : `Box2I`
        Return to return data for

    Returns
    -------
    iamge : `ImageF`
        The unbiased image
    """
    if bias_type is not None:
        image = imutil.unbias_and_trim(img, serial_oscan,
                                       bias_method=bias_type,
                                       bias_frame=superbias_im,
                                       imaging=region)
    else:
        image = img
        if superbias_im is not None:
            image -= superbias_im
        if region is not None:
            image = imutil.trim(image, region)

    return image

def raw_amp_image(butler, ccd, amp):
    """Get the image for a particular amp

    Parameters
    ----------
    butler : `Butler` or `None
        Data Butler
    ccd : `MaskedCCD` or `ImageF`
        CCD data object
    amp : `int`

    Returns
    -------
    iamge : `ImageF`
        The image
    """
    if ccd is not None:
        if butler is not None:
            image = get_raw_image(None, ccd, amp+1)
        else:
            image = get_raw_image(None, ccd, amp)
    else:
        image = None
    return image


def unbiased_ccd_image_dict(butler, ccd, **kwargs):
    """Get the images keys by amp for a ccd

    Parameters
    ----------
    butler : `Butler` or `None
        Data Butler
    ccd : `MaskedCCD` or `ImageF`
        CCD data object

    Keywords
    --------
    bias : `str` or `None`
        Method for bias subtraction
    superbias_frame : `MaskedCCD` or `None`
        Bias frame to subtract off

    Returns
    -------
    o_dict : `dict`
        Images keyed by amplifier index
    """
    kwcopy = kwargs.copy()
    bias_type = kwcopy.pop('bias', None)
    superbias_frame = kwcopy.pop('superbias_frame', None)

    amps = get_amp_list(butler, ccd)

    o_dict = {}
    for amp in amps:
        regions = get_geom_regions(butler, ccd, amp)
        serial_oscan = regions['serial_overscan']
        img = get_raw_image(butler, ccd, amp)
        superbias_im = raw_amp_image(butler, superbias_frame, amp)
        image = unbias_amp(img, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
        o_dict[amp] = image

    return o_dict


def extract_ccd_array_dict(butler, data_id, **kwargs):
    """Get the Geometry for a particular dataId or file

    Parameters
    ----------
    butler : `Butler` or `None
        Data Butler
    data_id : `dict` or `str`
        Data identifier or filename

    Keywords
    --------
    mask_files : `list`
        List of mask files
    bias : `str` or `None`
        Method for bias subtraction
    superbias_frame : `MaskedCCD` or `None`
        Bias frame to subtract off

    Returns
    -------
    o_dict : `dict`
        Arrays keyed by amplifier index
    """
    kwcopy = kwargs.copy()
    mask_files = kwcopy.pop('mask_files', [])
    ccd = get_ccd_from_id(None, data_id, mask_files)
    unbiased_images = unbiased_ccd_image_dict(butler, ccd, **kwargs)

    o_dict = {}
    for amp, image in unbiased_images.items():
        regions = get_geom_regions(butler, ccd, amp)
        frames = get_image_frames_2d(image, regions)
        o_dict[amp] = frames[kwcopy.pop('region', 'imaging')]

    return o_dict


def extract_raft_array_dict(butler, data_id_dict, **kwargs):
    """Get raft level data

    Parameters
    ----------
    butler : `Butler` or `None
        Data Butler
    data_id_dict : `dict`
        Dictionary, keyed by slot, of data identifiers or filenames

    Keywords
    --------
    mask_dict : `dict`
        Dictionary, keyed by slot, of lists of mask files
    bias : `str` or `None`
        Method for bias subtraction
    superbias_dict : `dict`
        Dictionary, keyed by slot, of Bias frames to subtract off

    Returns
    -------
    o_dict : `dict`
        Dictionary, keyed by slot, of CCD images
    """
    kwcopy = kwargs.copy()
    o_dict = {}
    mask_dict = kwcopy.pop('mask_dict', None)
    superbias_dict = kwcopy.pop('superbias_dict', None)

    for slot, data_id in data_id_dict.items():
        if mask_dict is None:
            mask_files = []
        else:
            mask_files = mask_dict[slot]
        if superbias_dict is None:
            superbias_frame = None
        else:
            superbias_frame = superbias_dict[slot]

        o_dict[slot] = extract_ccd_array_dict(butler, data_id,
                                              mask_files=mask_files,
                                              superbias_frame=superbias_frame,
                                              **kwcopy)
    return o_dict


def get_exposure_time(butler, ccd):
    """Return the exposure time

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler (or none)
    ccd : `ImageF` or `MaskedImageF`
        CCD image object

    Returns
    -------
    exptime : `float`
        The exposure time in seconds
    """
    if butler is None:
        return ccd.md.md.get('EXPTIME')
    raise NotImplementedError("Can't get exposure time for butlerlized data")

def get_mondiode_val(butler, ccd):
    """Return the monitoring diode value

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler (or none)
    ccd : `ImageF` or `MaskedImageF`
        CCD image object

    Returns
    -------
    val : `float`
        The value
    """
    if butler is None:
        return ccd.md.get('MONDIODE')
    raise NotImplementedError("Can't get mondiode value for butlerlized data")


def get_mono_wl(butler, ccd):
    """Return the monochromatic wavelength

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler (or none)
    ccd : `ImageF` or `MaskedImageF`
        CCD image object

    Returns
    -------
    val : `float`
        The value
    """
    if butler is None:
        return ccd.md.get('MONOWL')
    raise NotImplementedError("Can't get monowl for butlerlized data")


def stack_images(butler, in_files, statistic=afwMath.MEDIAN, **kwargs):
    """Stack a set of images

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler (or none)
    in_files : `list`
        Data to stack, either data_ids or filenames
    statistic : `int`
        Statisitic used to make superbias image

    Keywords
    --------
    bias_type : `str`
        Unbiasing method to use
    superbias_frame : `MaskedCCD` or `None`
        Bias image to subtract
    log : `log`
        Logging stream

    Returns
    -------
    out_dict : `dict`
        Mapping amplifier index to stacked image
    """

    bias_type = kwargs.get('bias_type', 'spline')
    superbias_frame = kwargs.get('superbias_frame', None)
    log = kwargs.get('log', None)

    amp_stack_dict = {}
    out_dict = {}

    exp_time = 0.0

    for ifile, in_file in enumerate(in_files):
        if ifile % 10 == 0:
            if log is not None:
                log.info("  %i" % ifile)

        ccd = get_ccd_from_id(butler, in_file, mask_files=[])
        exp_time += get_exposure_time(butler, ccd)
        amps = get_amp_list(butler, ccd)

        for amp in amps:
            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(butler, ccd, amp)
            superbias_im = raw_amp_image(butler, superbias_frame, amp)

            if ifile == 0:
                amp_stack_dict[amp] = [unbias_amp(img, serial_oscan,
                                                  bias_type=bias_type,
                                                  superbias_im=superbias_im)]
            else:
                amp_stack_dict[amp].append(unbias_amp(img, serial_oscan,
                                                      bias_type=bias_type,
                                                      superbias_im=superbias_im))

    exp_time /= len(in_files)
    out_dict['METADATA'] = dict(EXPTIME=exp_time)

    for key, val in amp_stack_dict.items():
        if butler is None:
            outkey = key
        else:
            outkey = key + 1
        stackimage = imutil.stack(val, statistic)
        out_dict[outkey] = stackimage

    if log is not None:
        log.info("Done!")

    return out_dict


def read_masks(maskfile):
    """Read masks for all amplifiers from a file

    Parameters
    ----------
    maskfile : `str`
        The file we are reading

    Returns
    -------
    mask_list : `list`
        The mask images we have read
    """
    mask_list = []
    for i in range(16):
        amask = AFWIMAGE_MASK(maskfile, i+1)
        mask_list.append(amask)
    return mask_list


def apply_masks(butler, ccd, maskfiles):
    """Apply a set of masks to an image (this is done in place)

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler
    ccd : `ExposureF` or `MaskedImageF`
        Image we are masking
    maskfiles : `list`
        Files with the masks we are applying
    """
    if butler is None:
        return
    geom = ccd.getDetector()
    for mfile in maskfiles:
        mask_list = read_masks(mfile)
        for amp, mask in enumerate(mask_list):
            (step_x, step_y) = get_geom_steps_from_amp(ccd, amp)
            ccd.mask[geom[amp].getRawBBox()].array = mask.array[::step_x, ::step_y]



def sort_sflats(butler, sflat_files):
    """Sort a set of superflat image filenames into low and high exposures

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler (or none)
    sflat_files : `list`
        List of superflat files

    Returns
    -------
    sflats_l : `list`
        Low exposure superflats
    sflats_h : `list`
        High exposure superflats
    """
    sflats_l = []
    sflats_h = []

    for sflat in sflat_files:
        if butler is None:
            if sflat.find('_L_') >= 0:
                sflats_l.append(sflat)
            elif sflat.find('flat_L') >= 0:
                sflats_l.append(sflat)
            elif sflat.find('_H_') >= 0:
                sflats_h.append(sflat)
            elif  sflat.find('flat_H') >= 0:
                sflats_h.append(sflat)

    return (sflats_l, sflats_h)


def outlier_stats(data_array, mean_val, max_offset):
    """Get some stats on the number of outliers in an array

    Parameters
    ----------
    data_array : `np.array`
        2D data array
    mean_val : `float`
        Expected value
    max_offset : `float`
        Maximum offset from mean

    Returns
    -------
    o_dict : `dict`
        Dictionary with information about outliers
    """
    mask_array = np.fabs(data_array - mean_val) > max_offset
    cols = mask_array.sum(0)
    rows = mask_array.sum(1)
    o_dict = dict(row_data=rows,
                  col_data=cols,
                  nbad_total=mask_array.sum()/data_array.size,
                  nbad_rows=(rows >= 10).sum()/rows.size,
                  nbad_cols=(cols >= 10).sum()/cols.size)
    return o_dict


def outlier_raft_dict(raft_data, mean_val, max_offset):
    """Get some stats on the number of outliers for a raft

    Parameters
    ----------
    data_array : `np.array`
        2D data array
    mean_val : `float`
        Expected value
    max_offset : `float`
        Maximum offset from mean

    Returns
    -------
    o_dict : `dict`
        Dictionary of dictionaries with information about outliers, keyed by slot
    """
    out_data = dict(nbad_total=[],
                    nbad_rows=[],
                    nbad_cols=[],
                    row_data=[],
                    col_data=[],
                    slot=[],
                    amp=[])

    for islot, (_, slot_arrays) in enumerate(sorted(raft_data.items())):
        for iamp, (_, ccd_data) in enumerate(sorted(slot_arrays.items())):
            outlier_data = outlier_stats(ccd_data, mean_val, max_offset)
            out_data['slot'].append(islot)
            out_data['amp'].append(iamp)
            for key, val in outlier_data.items():
                out_data[key].append(val)
    return out_data
