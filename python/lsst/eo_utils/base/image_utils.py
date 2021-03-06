"""This module contains functions to get particular bits of data out of images.
These functions will work both with Butlerized and un-Butlerized data.

"""

import os

import numpy as np

from scipy import fftpack

from astropy.io import fits

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

import lsst.afw.detection as afwDetect

import lsst.geom as afwGeom

from lsst.pex.exceptions.wrappers import LengthError

import lsst.eotest.image_utils as imutil
from lsst.eotest.sensor import MaskedCCD
from lsst.eotest.sensor.flatPairTask import mondiode_value

from .defaults import T_SERIAL, T_PARALLEL

# These are the names and labels for the parts of the data array
REGION_KEYS = ['i', 's', 'p']
REGION_NAMES = ['imaging', 'serial_overscan', 'parallel_overscan']
REGION_LABELS = ['Imaging region', 'Serial overscan', 'Parallel overscan']

try:
    AFWIMAGE_MASK = afwImage.MaskU
except AttributeError:
    AFWIMAGE_MASK = afwImage.Mask


def get_dims_from_ccd(ccd):
    """Get the CCD amp dimensions for a particular dataId or file

    Parameters
    ----------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    odict : `dict`
        Dictionary with the dimensions
    """
    if isinstance(ccd, MaskedCCD):
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


def get_readout_freqs_from_ccd(ccd):
    """Get the frequencies corresponding to the FFTs

    Parameters
    ----------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    odict : `dict`
        Dictionary with the frequencies
    """

    if isinstance(ccd, MaskedCCD):
        geom = ccd.amp_geom
        nrow_i = geom.imaging.getHeight()
        nrow_s = geom.serial_overscan.getHeight()
        nrow_p = geom.parallel_overscan.getHeight()
        ncol_i = geom.imaging.getWidth()
        ncol_s = geom.serial_overscan.getWidth()
        ncol_p = geom.parallel_overscan.getWidth()
        ncol_f = geom.naxis1
    else:
        geom = ccd.getDetector()[0]
        nrow_i = geom.getBBox().getHeight()
        nrow_s = geom.getRawHorizontalOverscanBBox().getHeight()
        nrow_p = geom.getRawVerticalOverscanBBox().getHeight()
        ncol_i = geom.getBBox().getWidth()
        ncol_s = geom.getRawHorizontalOverscanBBox().getWidth()
        ncol_p = geom.getRawVerticalOverscanBBox().getWidth()
        ncol_f = geom.getRawBBox().getWidth()

    t_row = ncol_f*T_SERIAL + T_PARALLEL
    f_s = 1./t_row
    f_c = 1/T_SERIAL

    o_dict = dict(freqs_i=fftpack.fftfreq(nrow_i)*f_s,
                  freqs_s=fftpack.fftfreq(nrow_s)*f_s,
                  freqs_p=fftpack.fftfreq(nrow_p)*f_s,
                  freqs_i_col=fftpack.fftfreq(ncol_i)*f_c,
                  freqs_s_col=fftpack.fftfreq(ncol_s)*f_c,
                  freqs_p_col=fftpack.fftfreq(ncol_p)*f_c)
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
    if isinstance(ccd, MaskedCCD):
        try:
            manu = ccd.md.get('CCD_MANU')
        except KeyError:
            manu = ccd.md.get('LSST_NUM')[0:3]
    else:
        manu = ccd.getDetector().getSerial()[0:3]

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
    manu = hdus[0].header.get('CCD_MANU', None)
    if manu is None:
        manu = hdus[0].header.get('LSST_NUM')[0:3]
    for amp in range(1, 17):
        (step_x, step_y) = get_geom_steps_manu_hdu(manu, amp)
        hdus[amp].data = hdus[amp].data[::step_x, ::step_y]
    hdus.writeto(filepath, overwrite=True)

def get_geom_regions(ccd, amp):
    """Get the ccd amp bounding boxes for a particular dataId or file

    Parameters
    ----------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object
    amp : `int`
        Amplifier index

    Returns
    -------
    odict : `dict`
        Dictionary with the bounding boxes
    """
    if isinstance(ccd, MaskedCCD):
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


def get_dimension_arrays_from_ccd(ccd):
    """Get the linear arrays with the indices for each direction and readout region

    Parameters
    ----------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    odict : `dict`
        Dictionary with the arrays
    """

    if isinstance(ccd, MaskedCCD):
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


def get_raw_image(ccd, amp):
    """Get the raw image for a particular amp

    Parameters
    ----------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object
    amp : `int`
        Amplifier index

    Returns
    -------
    odict : `ImageF`
        The image
    """
    if isinstance(ccd, MaskedCCD):
        img = ccd[amp]
    else:
        geom = ccd.getDetector()
        img = ccd.maskedImage[geom[amp].getRawBBox()]
    return img


def get_ccd_from_id(butler, data_id, mask_files, **kwargs):
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

    Keywords
    --------
    bias_frame : `ExposureF` or `MaskedCCD` or `None`
        Object with the bias data
    masked_ccd : `bool`
        Use bulter only to get filename, return as MaskedCCD object

    Returns
    -------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object
    """
    bias_frame = kwargs.get('bias_frame', None)
    if butler is None:
        exposure = MaskedCCD(str(data_id),
                             mask_files=mask_files,
                             bias_frame=bias_frame)
    elif kwargs.get('masked_ccd', False):
        filepath = butler.get('raw_filename', data_id)[0][0:-3]
        exposure = MaskedCCD(str(filepath),
                             mask_files=mask_files,
                             bias_frame=bias_frame)
    else:
        exposure = butler.get('raw', data_id)
        apply_masks(butler, exposure, mask_files)
    return exposure


def get_amp_list(ccd):
    """Get the Geometry for a particular dataId or file

    Parameters
    ----------
    ccd : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    amplist : `list`
        List of amplifier indices
    """
    if isinstance(ccd, MaskedCCD):
        amplist = list(ccd)
    else:
        amplist = range(16)
    return amplist


def get_amp_offset(ccd1, ccd2):
    """Get the Geometry for a particular dataId or file

    Parameters
    ----------
    ccd1 : `ExposureF` or `MaskedCCD`
        CCD data object
    ccd2 : `ExposureF` or `MaskedCCD`
        CCD data object

    Returns
    -------
    offter : `int`
        Offset to return
    """
    offset = 0
    if isinstance(ccd1, MaskedCCD):
        offset -= 1

    if isinstance(ccd2, MaskedCCD):
        offset += 1

    return offset





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


def get_data_as_read(ccd, amp, regionlist=None):
    """Split out the arrays for the serial_overscan, parallel_overscan, and imaging regions
    and return the data in the readout order.

    Parameters
    ----------
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
    raw_image = get_raw_image(ccd, amp)
    regions = get_geom_regions(ccd, amp)
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


def unbias_amp(img, serial_oscan, bias_type=None, superbias_im=None, region=None,
               bias_type_col=None, parallel_oscan=None):
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
                                       imaging=region,
                                       bias_method_col=bias_type_col,
                                       overscan_col=parallel_oscan)
    else:
        image = img
        if superbias_im is not None:
            image -= superbias_im
        if region is not None:
            image = imutil.trim(image, region)

    return image

def raw_amp_image(ccd, amp):
    """Get the image for a particular amp

    Parameters
    ----------
    ccd : `MaskedCCD` or `ImageF`
        CCD data object
    amp : `int`

    Returns
    -------
    iamge : `ImageF`
        The image
    """
    if ccd is not None:
        if not isinstance(ccd, MaskedCCD):
            image = get_raw_image(ccd, amp+1)
        else:
            image = get_raw_image(ccd, amp)
    else:
        image = None
    return image


def unbiased_ccd_image_dict(ccd, **kwargs):
    """Get the images keys by amp for a ccd

    Parameters
    ----------
    ccd : `MaskedCCD` or `ImageF`
        CCD data object

    Keywords
    --------
    bias : `str` or `None`
        Method for bias subtraction
    superbias_frame : `MaskedCCD` or `None`
        Bias frame to subtract off
    trim : `str` or `None`
        Region to trim return images to
    nonlinearity : `NonlinearityCorrection` or `None`
        Object that applies the nonlinearity correction

    Returns
    -------
    o_dict : `dict`
        Images keyed by amplifier index
    """
    kwcopy = kwargs.copy()
    bias_type = kwcopy.pop('bias', None)
    bias_type_col = kwcopy.pop('bias_col', None)
        
    superbias_frame = kwcopy.pop('superbias_frame', None)
    trim = kwcopy.pop('trim', None)
    nlc = kwcopy.pop('nonlinearity', None)

    amps = get_amp_list(ccd)

    is_masked_ccd = isinstance(ccd, MaskedCCD)

    o_dict = {}
    offset = get_amp_offset(ccd, superbias_frame)

    for amp in amps:
        regions = get_geom_regions(ccd, amp)
        serial_oscan = regions['serial_overscan']
        parallel_oscan = regions['parallel_overscan']
        if trim is None:
            trim_region = None
        else:
            trim_region = regions[trim]

        img = get_raw_image(ccd, amp)

        superbias_im = raw_amp_image(superbias_frame, amp + offset)
        if not is_masked_ccd and superbias_frame is not None:
            # Flip the superbias image for the subtraction
            (step_x, step_y) = get_geom_steps_from_amp(superbias_frame, amp + offset)
            superbias_im.mask.array = superbias_im.mask.array[::step_x, ::step_y]
            superbias_im.image.array = superbias_im.image.array[::step_x, ::step_y]

        image = unbias_amp(img, serial_oscan, bias_type=bias_type,
                           superbias_im=superbias_im, region=trim_region,
                           bias_type_col=bias_type_col, parallel_oscan=parallel_oscan)
        if nlc is not None:
            image.getImage().array[:] = nlc(amp, image.getImage().array)
        o_dict[amp] = image

    return o_dict


def extract_ccd_array_dict(data_id, **kwargs):
    """Get the Geometry for a particular dataId or file

    Parameters
    ----------
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
    o_dict = {}

    try:
        ccd = get_ccd_from_id(None, data_id, mask_files)
    except Exception:
        return o_dict

    unbiased_images = unbiased_ccd_image_dict(ccd, **kwargs)

    for amp, image in unbiased_images.items():
        regions = get_geom_regions(ccd, amp)
        frames = get_image_frames_2d(image, regions)
        o_dict[amp] = frames[kwcopy.pop('region', 'imaging')]

    return o_dict


def extract_raft_unbiased_images(data_id_dict, **kwargs):
    """Get the unbiased raft-level images

    Parameters
    ----------
    butler : `Butler` or `None
        Data Butler
    data_id : `dict`
        Dictionary, keyed by slot, amp of images

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
        Arrays keyed by slot, amp of images
    ccd_dict : `dict`
        CCD object, keyed by slot
    """
    kwcopy = kwargs.copy()
    o_dict = {}
    ccd_dict = {}
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
            kwcopy['superbias_frame'] = superbias_frame
        ccd = get_ccd_from_id(None, data_id, mask_files)
        ccd_dict[slot] = ccd
        o_dict[slot] = unbiased_ccd_image_dict(ccd, **kwcopy)
    return o_dict, ccd_dict


def extract_raft_array_dict(data_id_dict, **kwargs):
    """Get raft level data

    Parameters
    ----------
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

        o_dict[slot] = extract_ccd_array_dict(data_id,
                                              mask_files=mask_files,
                                              superbias_frame=superbias_frame,
                                              **kwcopy)
    return o_dict


def get_exposure_time(ccd):
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
    if isinstance(ccd, MaskedCCD):
        return ccd.md.md.get('EXPTIME')
    return ccd.getInfo().getVisitInfo().getExposureTime()


def compute_mondiode_flux_from_txt(pd_file, factor=5):
    """Return the monitoring diode computed from the txtfile

    Parameters
    ----------
    pd_file : `str`
        Filenaem of the text file in question

    Returns
    -------
    val : `float`
        The value
    """
    xvals, yvals = np.recfromtxt(pd_file).transpose()
    # Threshold for finding baseline current values:
    ythresh = (min(yvals) + max(yvals))/factor + min(yvals)
    # Subtract the median of the baseline values to get a calibrated
    # current.
    yvals -= np.median(yvals[np.where(yvals < ythresh)])
    integral = sum((yvals[1:] + yvals[:-1])/2*(xvals[1:] - xvals[:-1]))
    return integral


def get_mondiode_data(filepath, factor=5):
    """Get the monitoring diode data"""
    if filepath.find('.txt') >= 0:
        vals = np.recfromtxt(filepath)
        xvals = vals[:, 0]
        yvals = 1.0e9*vals[:, 1]
    else:
        with fits.open(filepath) as hdus:
            hdu = hdus['AMP0.MEAS_TIMES']
            xvals = hdu.data.field('AMP0_MEAS_TIMES')
            yvals = -1.0e9*hdu.data.field('AMP0_A_CURRENT')
    ythresh = (max(yvals) - min(yvals))/factor + min(yvals)
    index = np.where(yvals < ythresh)
    y_0 = np.median(yvals[index])
    yvals -= y_0
    return xvals, yvals


def avg_sum(times, currents):
    """Computing the photodiode charge as the product of the
    bin widths and the bin values.
    This is b/c the picoampmeter return the averaged time
    for each interval"""
    del_t = times[1:] - times[0:-1]
    return (currents[1:] * del_t).sum()

def get_mondiode_val(ccd):
    """Return the monitoring diode value

    Parameters
    ----------
    ccd : `ImageF` or `MaskedImageF`
        CCD image object

    Returns
    -------
    val : `float`
        The value
    """
    if isinstance(ccd, MaskedCCD):
        try:
            return mondiode_value(ccd.imfile, 0)
        except Exception as msg:
            print('mondiode_value functions failed, falling back to header keyword')
            print(msg)
        return ccd.md.get('MONDIODE')
    return ccd.getMetadata()['MONDIODE']


def get_monodiode_val_from_data_id(data_id, exp_time, teststand, butler):
    """Return the monitoring diode value

    Parameters
    ----------
    ccd : `ImageF` or `MaskedImageF`
        CCD image object

    exp_time : `float`
        Exposure time

    teststand : `str`
        The teststand (value are stored in different ways)

    butler : `Butler` or `None
        Data Butler

    Returns
    -------
    val : `float`
        The value
    """
    if butler is None:
        if teststand == 'ts8':
            mondiode_file = data_id
        elif teststand == 'bot':
            mondiode_file = os.path.join(os.path.dirname(data_id), 'Photodiode_Readings.txt')
    else:
        mondiode_file = os.path.join('analysis', 'bot', 'pd_calib',
                                     data_id['run'], "pd_calib_%s.txt" % data_id['visit'])

    try:
        mon_diode_x, mon_diode_y = get_mondiode_data(mondiode_file)
    except Exception:
        return None

    mon_diode_avg = avg_sum(mon_diode_y, mon_diode_x) / exp_time
    return mon_diode_avg


def get_mono_wl(ccd):
    """Return the monochromatic wavelength

    Parameters
    ----------
    ccd : `ImageF` or `MaskedImageF`
        CCD image object

    Returns
    -------
    val : `float`
        The value
    """
    if isinstance(ccd, MaskedCCD):
        return ccd.md.get('MONOWL')
    return ccd.getMetadata()['MONOWL']

def get_mono_slit_b(ccd):
    """Return the monochromatic slit wdith

    Parameters
    ----------
    ccd : `MaskedImageF` or `MaskedCCD`
        CCD image object

    Returns
    -------
    val : `float`
        The value
    """
    if isinstance(ccd, MaskedCCD):
        return ccd.md.get('MONOCH-SLIT_B')
    return ccd.getMetadata()['MONOCH-SLIT_B']


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
    bias_type_col = kwargs.get('bias_type_col', None)
    superbias_frame = kwargs.get('superbias_frame', None)
    log = kwargs.get('log', None)
    gains = kwargs.get('gains', None)
    nlc = kwargs.get('nlc', None)
    stat_ctrl = kwargs.get('stat_ctrl', None)
    if stat_ctrl is None:
        stat_ctrl = afwMath.StatisticsControl()

    amp_stack_dict = {}
    out_dict = {}

    exp_time = 0.0
    used_files = 0

    for ifile, in_file in enumerate(in_files):
        if ifile % 10 == 0:
            if log is not None:
                log.info("  %i" % ifile)

        try:
            ccd = get_ccd_from_id(butler, in_file, mask_files=[])
        except Exception:
            if log is not None:
                log.warn("  Failed to read %s, skipping" % (str(in_file)))
            continue

        used_files += 1
        exp_time += get_exposure_time(ccd)
        amps = get_amp_list(ccd)

        offset = get_amp_offset(ccd, superbias_frame)
        for iamp, amp in enumerate(amps):
            regions = get_geom_regions(ccd, amp)
            serial_oscan = regions['serial_overscan']
            parallel_oscan = regions['parallel_overscan']
            img = get_raw_image(ccd, amp)
            superbias_im = raw_amp_image(superbias_frame, amp + offset)
            unbiased = unbias_amp(img, serial_oscan,
                                  bias_type=bias_type,
                                  superbias_im=superbias_im,
                                  bias_type_col=bias_type_col,
                                  parallel_oscan=parallel_oscan)
            if gains is not None:
                unbiased.image.array *= gains[iamp]
            if nlc is not None:
                unbiased.image.array = nlc(unbiased.image.array)

            if ifile == 0:
                amp_stack_dict[amp] = [unbiased]
            else:
                amp_stack_dict[amp].append(unbiased)

    if used_files:
        exp_time /= float(used_files)
    else:
        return None

    out_dict['METADATA'] = dict(EXPTIME=exp_time)

    for key, val in amp_stack_dict.items():
        if butler is None:
            outkey = key
        else:
            outkey = key + 1
        stackimage = imutil.stack(val, statistic, stat_ctrl=stat_ctrl)
        out_dict[outkey] = stackimage.image

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



def sort_sflats(butler, sflat_files, exptime_cut=20.):
    """Sort a set of superflat image filenames into low and high exposures

    Parameters
    ----------
    butler : `Butler` or `None`
        Data Butler (or none)
    sflat_files : `list`
        List of superflat files
    exptime_cute : `float`
        Cut between low and high exposures

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
        else:
            exp_time = butler.queryMetadata('raw', 'EXPTIME', sflat)[0]
            if exp_time < exptime_cut:
                sflats_l.append(sflat)
            else:
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


def extract_raft_imaging_data(image_dict, ccd_dict, **kwargs):
    """Get data from the imaging regions

    Parameters
    ----------
    image_dict : `dict`
        Dictionary, keyed by slot, amp of images
    ccd_dict : `dict`
        Dictionary, keyed by slot, amp of CCD objects

    Returns
    -------
    o_dict : `dict`
        Dictionary, keyed by slot, amp of array data
    """
    kwcopy = kwargs.copy()
    o_dict = {}
    for slot, slot_data in image_dict.items():
        ccd = ccd_dict[slot]
        o_dict[slot] = {}
        for amp, image in slot_data.items():
            regions = get_geom_regions(ccd, amp)
            frames = get_image_frames_2d(image, regions)
            o_dict[slot][amp] = frames[kwcopy.pop('region', 'imaging')]

    return o_dict


def outlier_raft_dict(raft_data, mean_val, max_offset):
    """Get some stats on the number of outliers for a raft

    Parameters
    ----------
    raft_data : `dict`
        dictionary, keyed by slot, amp index of array data
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




def fill_footprint_dict(image, fp_dict, amp, slot, **kwargs):
    """Fill a dictionary with data about the footprints from an image

    Parameters
    ----------
    image : `imageF`
        The image we are analyzing

    fp_dict : `dict`
        The dictionary we are filling

    amp : `int`
        Amplifier index

    slot : `int`
        Slot index

    Keywords
    --------
    frac_thresh : float
        Threshold as a fraction of the median
    """
    kwcopy = kwargs.copy()
    fp_type = kwcopy.get('fp_type', 'dark')

    if fp_type == 'dark':
        frac_thresh = kwcopy.get('frac_thresh', 0.6)
        median = np.median(image.array)
        #stdev = np.std(image.array)
        thresh_float = frac_thresh*median
        thresh_0p2_float = (1. - (1. - frac_thresh)*0.2)*median
        threshold = afwDetect.Threshold(thresh_float)
        keystr = 'ratio'
    elif fp_type == 'bright':
        abs_thresh = kwcopy.get('abs_thresh', 50.)
        median = float(np.median(image.array))
        thresh_float = median + abs_thresh
        thresh_0p2_float = median + 0.2*abs_thresh
        threshold = afwDetect.Threshold(thresh_float)
        keystr = 'mean'

    fpset = afwDetect.FootprintSet(image, threshold)

    for footprint in fpset.getFootprints():
        bbox = footprint.getBBox()

        if bbox.getWidth() > 500:
            continue

        fp_dict['slot'].append(slot)
        fp_dict['amp'].append(amp)

        fp_dict['x_corner'].append(bbox.getMinX())
        fp_dict['y_corner'].append(bbox.getMinY())

        fp_dict['x_size'].append(bbox.getWidth())
        fp_dict['y_size'].append(bbox.getHeight())

        cutout = image[bbox].array
        peak_idx = cutout.argmax()

        peak_x = bbox.getMinX() + int(peak_idx % cutout.shape[1])
        peak_y = bbox.getMinY() + int(peak_idx / cutout.shape[1])
        fp_dict['x_peak'].append(peak_x)
        fp_dict['y_peak'].append(peak_y)

        peak = afwGeom.Point2I(peak_x, peak_y)
        extent = afwGeom.Extent2I(1, 1)
        bbox_expand = afwGeom.Box2I(peak, extent)

        ratio_full = np.mean(cutout)
        if fp_type == 'dark':
            ratio_full /= median

        fp_dict['%s_full' % keystr].append(ratio_full)

        npix_cumul = np.array([1, 8, 16, 24])
        sums = np.zeros((4))
        over_thresh = np.zeros((4), int)
        over_0p2_thresh = np.zeros((4), int)

        sums_cumul = np.zeros((4))
        over_thresh_cumul = np.zeros((4), int)
        over_0p2_thresh_cumul = np.zeros((4), int)

        for i in range(4):

            try:
                cuttout_array = image[bbox_expand].array
            except LengthError:
                break

            sums[i] = cuttout_array.sum()
            over_thresh[i] = (cuttout_array > thresh_float).sum()
            over_0p2_thresh[i] = (cuttout_array > thresh_0p2_float).sum()

            if i > 0:
                sums_cumul[i] = sums[i] - sums[i-1]
                over_thresh_cumul[i] = over_thresh[i] - over_thresh[i-1]
                over_0p2_thresh_cumul[i] = over_0p2_thresh[i] - over_0p2_thresh[i-1]
            else:
                sums_cumul[i] = sums[i]
                over_thresh_cumul[i] = over_thresh[i]
                over_0p2_thresh_cumul[i] = over_0p2_thresh[i]

            bbox_expand.grow(1)

        means_cumul = sums_cumul/npix_cumul

        if fp_type == 'dark':
            means_cumul /= median

        for i in range(4):
            fp_dict['%s_%i' % (keystr, i)].append(means_cumul[i])
            fp_dict['npix_%i' % i].append(over_thresh_cumul[i])
            fp_dict['npix_0p2_%i' % i].append(over_0p2_thresh_cumul[i])


def build_defect_dict(dark_array, **kwargs):
    """Extract information about the defects into a dictionary

    Parameters
    ----------
    dark_array : `dict`
        The images, keyed by slot, amp
    kwargs
        Used to override default configuration

    Returns
    -------
    out_dict : `dict`
        The output dictionary
    """
    fp_dict = dict(slot=[],
                   amp=[],
                   x_corner=[],
                   y_corner=[],
                   x_peak=[],
                   y_peak=[],
                   x_size=[],
                   y_size=[],
                   mean_full=[])
    for i in range(4):
        fp_dict['mean_%i' % i] = []
        fp_dict['npix_%i' % i] = []
        fp_dict['npix_0p2_%i' % i] = []

    for islot, (_, slot_data) in enumerate(sorted(dark_array.items())):
        for iamp, (_, image) in enumerate(sorted(slot_data.items())):
            fill_footprint_dict(image.image, fp_dict, iamp, islot, **kwargs)
    return fp_dict
