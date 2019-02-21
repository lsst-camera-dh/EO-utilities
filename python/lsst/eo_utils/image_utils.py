#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to get particular bits of data out of images"""

import lsst.eotest.image_utils as imutil


def get_image_frames_2d(img, amp_geom):
    """Split out the arrays for the serial_overscan, parallel_overscan, and imaging regions

    @param img (lsst.eotest.sensor.MaskedImageF) Data from one amplifier
    @param amp_geom (lsst.eotest.sensor.AmplifierGeometry.AmplifierGeometry) Geometry for that amp

    @returns (dict)
      i_array (numpy.narray) with the imaging section data
      p_array (numpy.narray) with the parallel overscan section data
      s_array (numpy.narray) with the serial overscan section data
    """
    s_oscan = amp_geom.serial_overscan
    p_oscan = amp_geom.parallel_overscan
    imaging = amp_geom.imaging
    s_array = img.Factory(img, s_oscan).getImage().getArray()
    p_array = img.Factory(img, p_oscan).getImage().getArray()
    i_array = img.Factory(img, imaging).getImage().getArray()

    o_dict = dict(i_array=i_array,
                  s_array=s_array,
                  p_array=p_array)

    return o_dict


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



def unbias(ccd, amp, oscan, bias_type=None, superbias_frame=None):
    """Unbias the data from a particular amp

    @param ccd (MaskedImageF)              The data
    @param amp (int)                       The amplified index
    @param oscan (AmplifierGeometry  )     Geometry for that amp
    @param bias_type (str)                 Method of unbiasing to applly
    @param superbias_frame (MaskedImageF)  Optional superbias frame to subtract off

    @returns (MaskedImageF) The unbiased image
    """
    if bias_type is not None:
        image = imutil.unbias_and_trim(ccd[amp], oscan.serial_overscan,
                                       bias_method=bias_type)
    else:
        image = ccd[amp]

    if superbias_frame is not None:
        image -= superbias_frame[amp]

    return image
