"""Functions to help make plots"""

import numpy as np
import matplotlib.pyplot as plt
import lsst.eotest.image_utils as imutil

from lsst.eotest.sensor import MaskedCCD


def setup_figure(xlabel, ylabel, figsize=(14, 8)):
    """Set up a 4x4 grid of plots with requested labeling

    Parameters
    ----------
    xlabel:     str
    ylabel:     str
    figsize:    tuple
       The figure width, height in inches

    Returns
    -------
    fig:        `matplotlib.figure.Figure`
    ax:         `matplotlib.Axes._subplots.AxesSubplot`
    """
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return (fig, ax)


def setup_amp_plots_grid(xlabel, ylabel, figsize=(14, 8)):
    """Set up a 4x4 grid of plots with requested labeling

    Parameters
    ----------
    xlabel:     str
    ylabel:     str
    figsize:    tuple
       with the figure width, height in inches

    Returns
    -------
    fig:        `matplotlib.figure.Figure`
    axs:        Array of `matplotlib.Axes._subplots.AxesSubplot`
    """
    fig_nrow = 4
    fig_ncol = 4
    fig, axs = plt.subplots(nrows=fig_nrow, ncols=fig_ncol, figsize=figsize)
    for i_row in range(fig_nrow):
        ax_row = axs[i_row, 0]
        ax_row.set_ylabel(ylabel)

    for i_col in range(fig_ncol):
        ax_col = axs[3, i_col]
        ax_col.set_xlabel(xlabel)
    return (fig, axs)


def setup_raft_plots_grid(xlabel, ylabel, figsize=(14, 8)):
    """Set up a 3x3 grid of plots with requested labeling

    xlabel:     str
       x-axis label for the plots
    ylabel:     str
       y-axis label for the plots
    figsize:    tuple
       figure width, height in inches

    returns:
    fig:        `matplotlib.figure.Figure`
    axs:        Array of `matplotlib.Axes._subplots.AxesSubplot`
    """
    fig_nrow = 3
    fig_ncol = 3
    fig, axs = plt.subplots(nrows=fig_nrow, ncols=fig_ncol, figsize=figsize)
    for i_row in range(fig_nrow):
        ax_row = axs[i_row, 0]
        ax_row.set_ylabel(ylabel)

    for i_col in range(fig_ncol):
        ax_col = axs[2, i_col]
        ax_col.set_xlabel(xlabel)
    return (fig, axs)


def plot_fft(ax, freqs, fftpow):
    """Plots the positive frequencies of an FFT

    Parameters
    ----------
    ax:         `matplotlib.Axes`
       Axes to plot on
    freqs:      `numpy.ndarray`
       The frequencies to be ploted on the x-axis
    fftpow:     `numpy.ndarray`
       The power corresponding to the frequencies
    """
    n_row = len(fftpow)
    ax.plot(freqs[0:n_row/2], fftpow[0:n_row/2])


def plot_hist(ax, data, xmin=-20, xmax=20, nbins=80):
    """Histograms data and plots it

    Parameters
    ----------
    ax:         `matplotlib.Axes`
       Axes to plot on
    data:       `numpy.ndarray`
       The frequencies to be ploted on the x-axis
    xmin:       float
    xmax:       float
    nbins:      int
    """
    hist = np.histogram(data, bins=nbins, range=(xmin, xmax))
    bins = (hist[1][0:-1] + hist[1][1:])/2.
    ax.plot(bins, hist[0])


def plot_stat_color(data, title, clabel, figsize=(14, 8), **kwargs):
    """Make a 2D color image of an array of data

    Parameters
    ----------
    data:       `numpy.ndarray`
       The data to be plotted
    title:      str
    clabel:     str
    figsize:    tuple

    Keyword arguments
    -----------------
    xlabel:     str
    ylabel:     str

    Returns
    -------
    fig:        `matplotlib.figure.Figure`
    ax:         `matplotlib.Axes._subplots.AxesSubplot`
    im:
    cbar:
    """
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)
    ax.set_xlabel(kwargs.pop('xlabel', "Amp. Index"))
    ax.set_ylabel(kwargs.pop('ylabel', "Slot Index"))
    im = ax.imshow(data, interpolation='nearest', **kwargs)
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel(clabel, rotation=-90, va='bottom')
    return dict(fig=fig, ax=ax, im=im, cbar=cbar)


def plot_sensor(sensor_file, mask_files, **kwargs):


    """Plot the data from all 16 amps on a sensor in a single figure

    Parameters
    ----------
    sensor_file:   str, name of the containing data to be plotted
    mask_files:    list, of files used to construct the mask


    Keyword arguments
    -----------------
    vmin:          float, minimum value for color axis
    vmax:          float, maximum value for color axis
    bias_method:   str, method used to subtract bias 'none', 'mean', 'row', 'func' or 'spline'.
    subtract_mean: bool, subtract mean value from each image

    Returns
    -------
    fig:        `matplotlib.figure.Figure`
    axs:        Array of `matplotlib.Axes._subplots.AxesSubplot`
    """

    vmin = kwargs.get('vmin', -10)
    vmax = kwargs.get('vmax', 10)
    bias_method = kwargs.get('bias_method', None)
    subtract_mean = kwargs.get('subtract_mean', False)

    all_amps = imutil.allAmps()
    ccd = MaskedCCD(sensor_file, mask_files=mask_files)

    fig, axs = plt.subplots(2, 8, figsize=(15, 10))
    axs = axs.ravel()

    if bias_method is not None:
        oscan = ccd.amp_geom.serial_overscan

    for amp in all_amps:
        idx = amp - 1
        if bias_method is not None:
            im = imutil.unbias_and_trim(ccd[amp], oscan, bias_method=bias_method)
            dd = im.getImage().getArray()
        else:
            im = ccd[amp]
            dd = im.getImage().getArray()

        if subtract_mean:
            dd -= dd.mean()

        axs[idx].imshow(dd, origin='low', interpolation='none', vmin=vmin, vmax=vmax)
        axs[idx].set_title('Amp {}'.format(amp))

    plt.tight_layout()
    return (fig, axs)


def historgram_array(sensor_file, mask_files,
                     xlabel, ylabel, nbins=100,
                     vmin=-10, vmax=10, region=None):
    """Plot the data from all 16 amps on a sensor in a single figure

    Parameters
    ----------
    sensor_file:   str
       name of the file containing data to be plotted
    mask_files:    list
       names of files used to construct the mask
    xlabel:        str
       x-axis label for the plots
    ylabel:        str y
       y-axis label for the plots
    vmin:          float
       minimum value for color axis
    vmax:          float
       maximum value for color axis
    bias_method:   str
       method used to subtract bias:  'none', 'mean', 'row', 'func' or 'spline'.
    subtract_mean: bool
       subtract mean value from each image

    Returns
    -------
    fig:        `matplotlib.figure.Figure`
    axs:        Array of `matplotlib.Axes._subplots.AxesSubplot`
    """
    all_amps = imutil.allAmps()
    ccd = MaskedCCD(sensor_file, mask_files=mask_files)

    fig, axs = setup_amp_plots_grid(xlabel, ylabel)

    if region is None:
        region = ccd.amp_geom.imaging

    for idx, amp in enumerate(all_amps):
        image = ccd[amp].getImage()
        dd = image.Factory(image, region).getArray()
        axs.flat[idx].hist(dd.flat, bins=nbins, range=(vmin, vmax))

    plt.tight_layout()
    return fig, axs
