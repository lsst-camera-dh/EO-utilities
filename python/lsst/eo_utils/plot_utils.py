"""Functions to help make plots"""

import numpy as np
import matplotlib.pyplot as plt
import lsst.eotest.image_utils as imutil

from lsst.eotest.sensor import MaskedCCD


class FigureDict(object):
    """Object to store figures"""
    def __init__(self):
        """C'tor"""
        self._fig_dict = {}

    def get_figure(self, key):
        """Return a figure

        @param key (str)   Key for the figure.
        @returns (matplotlib.figure.Figure) requested Figure
        """
        return self._fig_dict[key]['fig']

    def get_obj(self, key, key2):
        """Return some other object besides a figures

        @param key (str)   Key for the figure.
        @param key2 (str)  Key for the object

        @returns (object) requested object
        """
        return self._fig_dict[key][key2]

    def setup_figure(self, key, **kwargs):
        """Set up a figure with requested labeling

        @param key (str)   Key for the figure.
        @param kwargs (dict)
            title (str)    Figure title
            xlabel (str)   X-axis label
            ylabel (str)   Y-axis label
            figsize (str)  Figure width, height in inches

        @returns (dict)
            fig (matplotlib.figure.Figure)
            ax (matplotlib.Axes._subplots.AxesSubplot)
        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', None)
        ylabel = kwargs.get('ylabel', None)
        figsize = kwargs.get('figsize', (15, 10))

        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        if title is not None:
            fig.suptitle(title)
        if xlabel is not None:
            ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)

        o_dict = dict(fig=fig, ax=ax)
        self._fig_dict[key] = o_dict
        return o_dict


    def setup_amp_plots_grid(self, key, **kwargs):
        """Set up a 4x4 grid of plots with requested labeling

        @param key (str)   Key for the figure.
        @param kwargs (dict)
            title (str)    Figure title
            xlabel (str)   X-axis label
            ylabel (str)   Y-axis label
            figsize (str)  Figure width, height in inches

        @returns (dict)
            fig (matplotlib.figure.Figure)
            axs (array if matplotlib.Axes._subplots.AxesSubplot)
        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', None)
        ylabel = kwargs.get('ylabel', None)
        figsize = kwargs.get('figsize', (15, 10))

        fig_nrow = 4
        fig_ncol = 4
        fig, axs = plt.subplots(nrows=fig_nrow, ncols=fig_ncol, figsize=figsize)

        if title is not None:
            fig.suptitle(title)

        if ylabel is not None:
            for i_row in range(fig_nrow):
                ax_row = axs[i_row, 0]
                ax_row.set_ylabel(ylabel)

        if xlabel is not None:
            for i_col in range(fig_ncol):
                ax_col = axs[3, i_col]
                ax_col.set_xlabel(xlabel)

        o_dict = dict(fig=fig, axs=axs)
        self._fig_dict[key] = o_dict
        return o_dict


    def setup_raft_plots_grid(self, key, **kwargs):
        """Set up a 3x3 grid of plots with requested labeling

        @param kwargs (dict)
            title (str)    Figure title
            xlabel (str)   X-axis label
            ylabel (str)   Y-axis label
            figsize (str)  Figure width, height in inches

        @returns (tuple)
            fig (matplotlib.figure.Figure)
            axs (array if matplotlib.Axes._subplots.AxesSubplot)
        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', None)
        ylabel = kwargs.get('ylabel', None)
        figsize = kwargs.get('figsize', (15, 10))

        fig_nrow = 3
        fig_ncol = 3
        fig, axs = plt.subplots(nrows=fig_nrow, ncols=fig_ncol, figsize=figsize)

        if title is not None:
            fig.suptitle(title)

        if ylabel is not None:
            for i_row in range(fig_nrow):
                ax_row = axs[i_row, 0]
                ax_row.set_ylabel(ylabel)

        if xlabel is not None:
            for i_col in range(fig_ncol):
                ax_col = axs[2, i_col]
                ax_col.set_xlabel(xlabel)

        o_dict = dict(fig=fig, axs=axs)
        self._fig_dict[key] = o_dict
        return o_dict


    def plot_fft(self, key, iamp, freqs, fftpow):
        """Plots the positive frequencies of an FFT

        @param key (str)              Key for the figure.
        @param iamp (int)             Amp index
        @param freqs (numpy.ndarray)  The frequencies to be ploted on the x-axis
        @param fftpow (numpy.ndarray) The power corresponding to the frequencies
        """
        n_row = len(fftpow)
        ax = self._fig_dict[key]['axs'].flat[iamp]
        ax.plot(freqs[0:n_row/2], fftpow[0:n_row/2])

    def plot_hist(self, key, iamp, data, **kwargs):
        """Histograms data and plots it

        @param key (str)              Key for the figure.
        @param iamp (int)             Amp index
        @param data (numpy.ndarray)   Data to histogram
        @param kwargs (dict)
            xmin (float)
            xmax (float)
            nbins (int)
        """
        xmin = kwargs.get('xmin', None)
        xmax = kwargs.get('xmin', None)
        if xmin is not None and xmax is not None:
            xr = (xmin, xmax)
        else:
            xr = None

        hist = np.histogram(data, bins=kwargs['nbins'], range=xr)
        bins = (hist[1][0:-1] + hist[1][1:])/2.
        ax = self._fig_dict[key]['axs'].flat[iamp]
        ax.plot(bins, hist[0])

    def plot(self, key, iamp, xdata, ydata):
        """Plot x versus y data for one amp

        @param key (str)               Key for the figure.
        @param iamp (int)              Amp index
        @param xdata (numpy.ndarray)   Data to histogram
        @param ydata (numpy.ndarray)   Data to histogram
        """
        self._fig_dict[key]['axs'].flat[iamp].plot(xdata, ydata)

    def plot_single(self, key, xdata, ydata):
        """Plot x versus y data

        @param key (str)               Key for the figure.
        @param xdata (numpy.ndarray)   Data to histogram
        @param ydata (numpy.ndarray)   Data to histogram
        """
        self._fig_dict[key]['ax'].plot(xdata, ydata)

    def plot_stat_color(self, key, data, **kwargs):
        """Make a 2D color image of an array of data

        @param key (str)               Key for the figure.
        @param data (numpy.ndarray)    The data to be plotted
        @param kwargs
          title (str)
          clabel (str)
          figsize (tuple)
          xlabel (str)
          ylabel (str)

        @returns (dict)
           fig (matplotlib.figure.Figure)
           ax (matplotlib.Axes._subplots.AxesSubplot)
           im
           cbar
        """
        title = kwargs.get('title', None)
        clabel = kwargs.get('clabel', None)
        figsize = kwargs.get('figsize', (14, 8))
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        ax.set_xlabel(kwargs.pop('xlabel', "Amp. Index"))
        ax.set_ylabel(kwargs.pop('ylabel', "Slot Index"))
        im = ax.imshow(data, interpolation='nearest', **kwargs)
        if title is not None:
            ax.set_title(title)
        cbar = fig.colorbar(im, ax=ax)
        if clabel is not None:
            cbar.ax.set_ylabel(clabel, rotation=-90, va='bottom')
        o_dict = dict(fig=fig, ax=ax, im=im, cbar=cbar)
        self._fig_dict[key] = o_dict
        return o_dict

    def plot_sensor(self, key, sensor_file, mask_files, **kwargs):
        """Plot the data from all 16 amps on a sensor in a single figure

        @param key (str)          Key for the figure.
        @param sensor_file (str)  name of the file containing data to be plotted
        @param mask_files (list)  names of files used to construct the mask
        @param kwargs
            vmin (float)          minimum value for color axis
            vmax (float)          maximum value for color axis
            bias (str)            method used to subtract bias 'none', 'mean', 'row', 'func' or 'spline'.
            superbias (str)       file with superbias image to subtract
            subtract_mean (bool)  Flag to subtract mean value from each image

        @returns (dict)
            fig (matplotlib.figure.Figure)
            axs (Array of `matplotlib.Axes._subplots.AxesSubplot)
        """
        vmin = kwargs.get('vmin', -10)
        vmax = kwargs.get('vmax', 10)
        bias_method = kwargs.get('bias', None)
        superbias = kwargs.get('superbias', None)
        subtract_mean = kwargs.get('subtract_mean', False)

        all_amps = imutil.allAmps()
        ccd = MaskedCCD(str(sensor_file), mask_files=mask_files)

        if superbias is None:
            superbias_frame = None
        else:
            superbias_frame = MaskedCCD(str(superbias))

        fig, axs = plt.subplots(2, 8, figsize=(15, 10))
        axs = axs.ravel()

        if bias_method is not None:
            oscan = ccd.amp_geom.serial_overscan

        for amp in all_amps:
            idx = amp - 1
            if bias_method is not None:
                im = imutil.unbias_and_trim(ccd[amp], oscan, bias_method=bias_method)
            else:
                im = ccd[amp]

            if superbias_frame is not None:
                im -= superbias_frame[amp]

            dd = im.getImage().getArray()
            if subtract_mean:
                dd -= dd.mean()

            axs[idx].imshow(dd, origin='low', interpolation='none', vmin=vmin, vmax=vmax)
            axs[idx].set_title('Amp {}'.format(amp))

        plt.tight_layout()
        o_dict = dict(fig=fig, axs=axs)
        self._fig_dict[key] = o_dict
        return o_dict


    def histogram_array(self, key, sensor_file, mask_files, **kwargs):
        """Plot the data from all 16 amps on a sensor in a single figure

        @param key (str)          Key for the figure.
        @param sensor_file (str)  name of the file containing data to be plotted
        @param mask_files (list)  names of files used to construct the mask
        @param kwargs
            vmin (float)          minimum value for x-axis
            vmax (float)          maximum value for x-axis
            nbins (int)           number of bins to use in historam
            bias (str)            method used to subtract bias 'none', 'mean', 'row', 'func' or 'spline'.
            superbias (str)       file with superbias image to subtract
            subtract_mean (bool)  Flag to subtract mean value from each image

        @returns (dict)
            fig (matplotlib.figure.Figure)
            axs (Array of `matplotlib.Axes._subplots.AxesSubplot)

        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', None)
        ylabel = kwargs.get('ylabel', None)
        vmin = kwargs.get('vmin', -10.)
        vmax = kwargs.get('vmax', 10.)
        nbins = kwargs.get('nbins', 200)
        bias_method = kwargs.get('bias', None)
        superbias = kwargs.get('superbias', None)
        subtract_mean = kwargs.get('subtract_mean', False)
        region = kwargs.get('region', None)

        ccd = MaskedCCD(str(sensor_file), mask_files=mask_files)

        if superbias is None:
            superbias_frame = None
        else:
            superbias_frame = MaskedCCD(str(superbias))

        if region is None:
            region = ccd.amp_geom.imaging

        if bias_method is not None:
            oscan = ccd.amp_geom.serial_overscan

        o_dict = self.setup_amp_plots_grid(key, title=title, xlabel=xlabel, ylabel=ylabel)
        axs = o_dict['axs']

        for idx, amp in enumerate(ccd):
            if bias_method is not None:
                im = imutil.unbias_and_trim(ccd[amp], oscan, bias_method=bias_method)
            else:
                im = ccd[amp]

            if superbias_frame is not None:
                im -= superbias_frame[amp]

            dd = im.Factory(im, region).getImage().getArray()
            if subtract_mean:
                dd -= dd.mean()

            axs.flat[idx].hist(dd.flat, bins=nbins, range=(vmin, vmax))

        plt.tight_layout()

        self._fig_dict[key] = o_dict
        return o_dict


    def savefig(self, key, filename):
        """Save a single figure

        @param key (str)          Key for the figure.
        @param filename (str)     Name of the output file
        """
        fig = self._fig_dict[key]['fig']
        fig.savefig(filename)
        plt.close(fig)

    def save_all(self, basename):
        """Save all the figures

        The files will be named {basename}_{key}.png

        @param basename (str)     Base of the output file names
        """
        for key, val in self._fig_dict.items():
            fig = val['fig']
            fig.savefig("%s_%s.png" % (basename, key))
            plt.close(fig)
