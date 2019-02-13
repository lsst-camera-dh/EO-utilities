"""Some functions to get particular bits of data out of images"""

def get_image_frames_2d(img, amp_geom):
    """Split out the arrays for the serial_overscan, parallel_overscan, and imaging regions

    Parameters
    ----------
    img:       `lsst.eotest.sensor.MaskedImageF`
       object with data from one amplifier
    amp_geom:  `lsst.eotest.sensor.AmplifierGeometry.AmplifierGeometry`
       object

    Returns
    -------
    i_array:   `numpy.narray`
       with the imaging section data
    p_array:   `numpy.narray`
       with the parallel overscan section data
    s_array:   `numpy.narray`
       with the serial overscan section data
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

    Parameters
    ----------
    i_array:  `numpy.narray`
       The input data
    clip:     tuple
       min and max used to clip the data, None implies no clipping
    do_std:   bool
       If true this will return the standard deviation instead of the mean

    Returns
    -------
    rows:    `numpy.narray`
       Row-wise means (or standard deviations)
    cols:    `numpy.narray`
       Col-wise means (or standard deviations)
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
