"""This module contains functions to get particular bits of data out of images.
These functions will work both with Butlerized and un-Butlerized data.

"""

import sys

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
    afwImage_Mask = afwImage.MaskU
except AttributeError:
    afwImage_Mask = afwImage.Mask


def get_dims_from_ccd(butler, ccd):
    """Get the CCD amp dimensions for a particular dataId or file

    @param butler (`Butler`)                      Data Butler (or none)
    @param ccd (`ExposureF` or `MaskedCCD`)       CCD data object

    @returns (dict) with the dimensions
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


def get_readout_frequencies_from_ccd(butler, ccd):
    """Get the frequencies corresponding to the FFTs

    @param butler (`Butler`)                      Data Butler (or none)
    @param ccd (`ExposureF` or `MaskedCCD`)       CCD data object

    @returns (dict) with the arrays of the frequencies
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

    @param manu (str)              ITL or E2V
    @param amp (int)               HDU index

    @returns (tuple)
        step_x (int)
        step_y (int)
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

    @param ccd (`ExposureF`)        CCD data object
    @param amp (int)                Amplifier number

    @returns (tuple)
        step_x (int)
        step_y (int)
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

    @param filepath (str)      The file we are adjusting
    """
    hdus = fits.open(filepath)
    manu = hdus[0].header['CCD_MANU']
    for amp in range(1, 17):
        (step_x, step_y) = get_geom_steps_manu_hdu(manu, amp)
        hdus[amp].data = hdus[amp].data[::step_x, ::step_y]
    hdus.writeto(filepath, overwrite=True)


def get_geom_regions(butler, ccd, amp):
    """Get the ccd amp bounding boxes for a particular dataId or file

    @param butler (`Butler`)                          Data Butler (or none)
    @param ccd (`ExposureF` or `MaskedCCD`)           CCD data object
    @param geom (`Detector` or `AmplifierGeometry`)   Object with the geometry
    @param amp (int)                                  Amplifier index

    @returns (dict) with the bounding boxes
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

    @param butler (`Butler`)                          Data Butler (or none)
    @param geom (`Detector` or `AmplifierGeometry`)   Object with the geometry

    @returns (dict) with the arrays
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

    @param butler (`Butler`)                  Data Butler (or none)
    @param ccd (`ExposureF` or `MaskedCCD`)   CCD data object
    @param amp (int)                          AmplifierIndex
    """
    if butler is None:
        im = ccd[amp].getImage()
    else:
        geom = ccd.getDetector()
        im = ccd.maskedImage[geom[amp].getRawBBox()].image
    return im


def get_ccd_from_id(butler, dataId, mask_files):
    """Get the Geometry for a particular dataId or file

    @param butler (`Butler`)     Data Butler (or none)
    @param dataId (dict or str)  Data identifier
    @param mask_files (list)     List of mask files

    @returns (`MaskedCCD` or `ExposureF`) CCD image
    """
    if butler is None:
        exposure = MaskedCCD(str(dataId), mask_files=mask_files)
    else:
        exposure = butler.get('raw', dataId)
        apply_masks(butler, exposure, mask_files)
    return exposure


def get_amp_list(butler, ccd):
    """Get the Geometry for a particular dataId or file

    @param butler (`Butler`)                  Data Butler (or none)
    @param ccd (`ExposureF` or `MaskedCCD)    CCD data object

    @returns (list) list of amplifier indices
    """
    if butler is None:
        amplist = [amp for amp in ccd]
    else:
        amplist = [amp for amp in range(16)]
    return amplist


def get_image_frames_2d(img, regions, regionlist=None):
    """Split out the arrays for the serial_overscan, parallel_overscan, and imaging regions

    @param img (`ImageF`)                   Image Data
    @param regions (dict)                   Geometry Object
    @param regionlist (list)                List of regions

    @returns (dict)
      (str):(numpy.narray) with the data or each region
    """
    step_x = regions['step_x']
    step_y = regions['step_y']

    if regionlist is None:
        regionlist = ['imaging', 'serial_overscan', 'parallel_overscan']

    try:
        o_dict = {key:img[regions[key]].getArray()[::step_x, ::step_y] for key in regionlist}
    except AttributeError:
        o_dict = {key:img[regions[key]].getImage().getArray()[::step_x, ::step_y] for key in regionlist}
    return o_dict


def get_data_as_read(butler, ccd, amp, regionlist=None):
    """Split out the arrays for the serial_overscan, parallel_overscan, and imaging regions
    and return the data in the readout order.

    @param butler (`Butler`)                 Data Butler (or none)
    @param ccd (`MaskedImageF`)              Data identifier
    @param amp (int)                         Amplifier index
    @param regionlist (list)                 List of regions

    @returns (dict)
      (str):(numpy.narray) with the data or each region
    """
    raw_image = get_raw_image(butler, ccd, amp)
    regions = get_geom_regions(butler, ccd, amp)
    frames = get_image_frames_2d(raw_image, regions, regionlist)
    return frames


def array_struct(i_array, clip=None, do_std=False):
    """Extract the row-by-row and col-by-col mean (or standard deviation)

    @param i_array (numpy.narray)  The input data
    @param clip (tuple)            min and max used to clip the data, None implies no clipping
    @param do_std (bool)           If true return the standard deviation instead of the mean

    @returns (dict)
       rows (numpy.narray)  Row-wise means (or standard deviations)
       cols (numpy.narray)  Col-wise means (or standard deviations)
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


def unbias_amp(im, serial_oscan, bias_type=None, superbias_im=None, region=None):
    """Unbias the data from a particular amp

    @param ccd (ImageF)                    The data
    @param serial_oscan (Box2I)            Serial overscan bounding box
    @param bias_type (str)                 Method of unbiasing to applly
    @param superbias_im (ImageF)           Optional superbias frame to subtract off

    @returns (MaskedImageF) The unbiased image
    """
    if bias_type is not None:
        image = imutil.unbias_and_trim(im, serial_oscan,
                                       bias_method=bias_type,
                                       bias_frame=superbias_im,
                                       imaging=region)
    else:
        image = im
        if superbias_im is not None:
            image -= superbias_im
        if region is not None:
            image = imutils.trim(image, region)

    return image


def make_superbias(butler, bias_files, statistic=afwMath.MEDIAN, **kwargs):
    """Make a set of superbias images

    @param butler (`Butler`)     Data Butler (or none)
    @param bias_files (dict)     Data used to make superbias
    @param statistic (int)       Statisitic used to make superbias image
    @param kwargs
    bias_type (str)    Unbiasing method to use

    @returns (dict) mapping amplifier index to suberbias image
    """

    bias_type = kwargs.get('bias_type', 'spline')

    amp_stack_dict = {}
    sbias_dict = {}

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files=[])
        amps = get_amp_list(butler, ccd)

        for amp in amps:
            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            im = get_raw_image(butler, ccd, amp)
            if ifile == 0:
                amp_stack_dict[amp] = [unbias_amp(im, serial_oscan, bias_type=bias_type)]
            else:
                amp_stack_dict[amp].append(unbias_amp(im, serial_oscan, bias_type=bias_type))


    for key, val in amp_stack_dict.items():
        if butler is None:
            outkey = key
        else:
            outkey = key + 1
        stackimage = imutil.stack(val, statistic)
        sbias_dict[outkey] = stackimage

    return sbias_dict


def read_masks(maskfile):
    """Read a list of masks

    @param maskfile (str)  The file we are reading

    @returns (list)  The mask images we have read
    """
    mask_list = []
    for i in range(16):
        amask = afwImage_Mask(maskfile, i+1)
        mask_list.append(amask)
    return mask_list


def apply_masks(butler, ccd, maskfiles):
    """Apply a set of masks to an image (this is done in place)

    @param butler (`Butler`)       Data Butler (or none)
    @param ccd (`MaskedImageF`)    Data identifier
    @param maskfiles (list)        The masks we are applying
    """
    if butler is None:
        return
    geom = ccd.getDetector()
    for mfile in maskfiles:
        mask_list = read_masks(mfile)
        for amp, mask in enumerate(mask_list):
            (step_x, step_y) = get_geom_steps_from_amp(ccd, amp)
            ccd.mask[geom[amp].getRawBBox()].array = mask.array[::step_x, ::step_y]
