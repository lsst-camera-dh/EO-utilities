"""Functions to help make plots"""

import numpy as np

import astropy.visualization as viz
from astropy.visualization.mpl_normalize import ImageNormalize

import lsst.eotest.image_utils as imutil
from .image_utils import get_ccd_from_id

from . import mpl_utils

from matplotlib import ticker
import matplotlib.pyplot as plt

mpl_utils.set_plt_ioff()

TESTCOLORMAP = dict(DARK="black",
                    FLAT="blue",
                    TRAP="red",
                    LAMBDA="magenta",
                    SFLAT="green",
                    SFLAT_500="green",
                    FE55="cyan")


class FigureDict:
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


    def setup_region_plots_grid(self, key, **kwargs):
        """Set up a 3x2 grid of plots with requested labeling

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

        fig_nrow = 2
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
                ax_col = axs[1, i_col]
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
        ax.plot(freqs[0:int(n_row/2)], fftpow[0:int(n_row/2)])

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

    def plot(self, key, iamp, xdata, ydata, **kwargs):
        """Plot x versus y data for one amp

        @param key (str)               Key for the figure.
        @param iamp (int)              Amp index
        @param xdata (numpy.ndarray)   Data to histogram
        @param ydata (numpy.ndarray)   Data to histogram
        @param kwargs                  Passed to matplotlib
        """
        self._fig_dict[key]['axs'].flat[iamp].plot(xdata, ydata, **kwargs)


    def plot_stats_band_amp(self, key, iamp, xvals, **kwargs):
        """Plot the data each amp in a set of runs in a single chart

        @param key (str)          Key for the figure.
        @param iamp (int)         Amp index
        @param kwargs:
            mean (array)
            median (array)
            std (array)
            min (array)
            max (array)
        """
        means = kwargs.pop('means')
        stds = kwargs.pop('stds')

        ax = self._fig_dict[key]['axs'].flat[iamp]
        ax.fill_between(xvals, kwargs.pop('mins'), kwargs.pop('maxs'), color='green')
        ax.fill_between(xvals, means-stds, means+stds, color='yellow')
        ax.plot(xvals, kwargs.pop('medians'), '.')


    def plot_single(self, key, xdata, ydata):
        """Plot x versus y data

        @param key (str)               Key for the figure.
        @param xdata (numpy.ndarray)   Data to histogram
        @param ydata (numpy.ndarray)   Data to histogram
        """
        self._fig_dict[key]['ax'].plot(xdata, ydata)

    def plot_xy_axs_from_tabledict(self, fd, key, idx, plotkey, **kwargs):
        """Plot x versus y data

        @param fd (TableDict)          Data
        @param key (str)               Key for the data
        @param idx (int)               Axes index
        @param plotkey (str)           Key for the plot
        @param kwargs:
           x_name (str) Name for the x-axis data
           y_name (str) Start of the name for the y-axis data
        """
        x_name = kwargs.get('x_name', 'x')
        y_name = kwargs.get('y_name', 'y')

        file_data = fd.get_table('files')
        df = fd.get_table(key)
        xcol = df[x_name]
        for col in df.columns:
            if col.find(y_name) != 0:
                continue
            valarray = df[col]
            for row, test_type in zip(valarray.T, file_data['testtype']):
                self.plot(plotkey, idx, xcol, row,
                          color=TESTCOLORMAP.get(test_type, 'gray'))


    def plot_xy_from_tabledict(self, fd, key, plotkey, **kwargs):
        """Plot x versus y data

        @param fd (TableDict)          Data
        @param key (str)               Key for the data
        @param plotkey (str)           Key for the plot
        @param kwargs:
           x_name (str) Name for the x-axis data
           y_name (str) Start of the name for the y-axis data
        """
        x_name = kwargs.get('x_name', 'x')
        y_name = kwargs.get('y_name', 'y')

        df = fd.get_table(key)
        xcol = df[x_name]
        for col in df.columns:
            if col.find(y_name) != 0:
                continue
            self.plot_single(plotkey, xcol, df[col])


    def plot_xy_amps_from_tabledict(self, fd, key, plotkey, **kwargs):
        """Plot x versus y data

        @param fd (TableDict)          Data
        @param key (str)               Key for the data
        @param plotkey (str)           Key for the plot
        @param kwargs:
           x_name (str) Name for the x-axis data
           y_name (str) Start of the name for the y-axis data
        """
        x_name = kwargs.get('x_name', 'x')
        y_name = kwargs.get('y_name', 'y')

        file_data = fd.get_table('files')
        df = fd.get_table(key)
        xcol = df[x_name]
        for col in df.columns:
            if col.find(y_name) != 0:
                continue
            amp = int(col.split('_')[-1][1:])
            valarray = df[col]
            if len(valarray.shape) == 1:
                rows = [valarray]
                ttypes = [file_data['testtype'][0]]
            else:
                rows = valarray.T
                ttypes = file_data['testtype']
            for row, test_type in zip(rows, ttypes):
                try:
                    color = TESTCOLORMAP[test_type]
                except KeyError:
                    color = "gray"

                self.plot(plotkey, amp, xcol, row, color=color)


    def plot_raft_correl_matrix(self, key, data, **kwargs):
        """Plot x versus y data

        @param key (str)               Key for the figure.
        @param data (numpy.ndarray)    Data to histogram
        @param kwargs
           slots (list)          Names of the slots
           title (str)           Title for the figure
           figsize (tuple)       Figure width, height in inches
           vmin (float)          minimum value for color axis
           vmax (float)          maximum value for color axis
        """
        slots = kwargs.get('slots', None)
        title = kwargs.get('title', None)
        vmin = kwargs.get('vmin', None)
        vmax = kwargs.get('vmax', None)
        figsize = kwargs.get('figsize', (14, 8))
        if vmin is not None and vmax is not None:
            vrange = (vmin, vmax)
        else:
            interval = viz.PercentileInterval(98.)
            vrange = interval.get_limits(np.abs(data.flatten()))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)

        if title is not None:
            ax.set_title(title)

        norm = ImageNormalize(vmin=vrange[0], vmax=vrange[1])
        im = ax.imshow(data, interpolation='none', norm=norm)
        cbar = plt.colorbar(im)

        if slots is not None:
            amps = 16
            major_locs = [i*amps - 0.5 for i in range(len(slots) + 1)]
            minor_locs = [amps//2 + i*amps for i in range(len(slots))]
            for axis in (ax.xaxis, ax.yaxis):
                axis.set_tick_params(which='minor', length=0)
                axis.set_major_locator(ticker.FixedLocator(major_locs))
                axis.set_major_formatter(ticker.FixedFormatter(['']*len(major_locs)))
                axis.set_minor_locator(ticker.FixedLocator(minor_locs))
                axis.set_minor_formatter(ticker.FixedFormatter(slots))

        o_dict = dict(fig=fig, ax=ax, im=im, cbar=cbar)
        self._fig_dict[key] = o_dict
        return o_dict

    def plot_stat_color(self, key, data, **kwargs):
        """Make a 2D color image of an array of data

        @param key (str)               Key for the figure.
        @param data (numpy.ndarray)    The data to be plotted
        @param kwargs
          title (str)                  Figure title
          clabel (str)                 Label for the colorbar
          figsize (tuple)              Figure width, height in inches
          xlabel (str)                 x-axis label
          ylabel (str)                 y-axis label

        @returns (dict)
           fig (matplotlib.figure.Figure)
           ax (matplotlib.Axes._subplots.AxesSubplot)
           im
           cbar
        """
        title = kwargs.get('title', None)
        clabel = kwargs.pop('clabel', None)
        figsize = kwargs.pop('figsize', (14, 8))
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
        butler = kwargs.get('butler', None)

        all_amps = imutil.allAmps()

        ccd = get_ccd_from_id(butler, sensor_file, mask_files)

        if superbias is None:
            superbias_frame = None
        else:
            superbias_frame = get_ccd_from_id(None, superbias, mask_files)

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
        vmin = kwargs.get('vmin', -10.)
        vmax = kwargs.get('vmax', 10.)
        nbins = kwargs.get('nbins', 200)
        bias_method = kwargs.get('bias', None)
        superbias = kwargs.get('superbias', None)
        subtract_mean = kwargs.get('subtract_mean', False)
        region = kwargs.get('region', None)
        butler = kwargs.get('butler', None)

        ccd = get_ccd_from_id(butler, sensor_file, mask_files)

        if superbias is None:
            superbias_frame = None
        else:
            superbias_frame = get_ccd_from_id(None, superbias, mask_files)

        if region is None:
            region = ccd.amp_geom.imaging

        if bias_method is not None:
            oscan = ccd.amp_geom.serial_overscan

        o_dict = self.setup_amp_plots_grid(key, **kwargs)

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

            ax = axs.flat[idx]
            ax.hist(dd.flat, bins=nbins, range=(vmin, vmax))

        plt.tight_layout()

        self._fig_dict[key] = o_dict
        return o_dict


    def plot_run_chart(self, key, runs, yvals, **kwargs):
        """Plot the data each amp in a set of runs in a single chart

        @param key (str)          Key for the figure.
        @param runs (array)       Aray of the run info
        @param yvals (list)       Values being plotted
        @param kwargs
            title (str)           Figure title
            clabel (str)          Label for the colorbar
            figsize (tuple)       Figure width, height in inches
            ylabel (str)          y-axis label
            vmin (float)          minimum value for color axis
            vmax (float)          maximum value for color axis
            bias (str)            method used to subtract bias 'none', 'mean', 'row', 'func' or 'spline'.
        """
        kwcopy = kwargs.copy()
        yerrs = kwcopy.pop('yerrs', None)
        title = kwcopy.pop('title', None)
        fig = plt.figure(figsize=kwcopy.pop('figsize', (14, 8)))
        ax = fig.add_subplot(111)

        if title is not None:
            ax.set_title(title)

        ax.set_ylabel(kwcopy.pop('ylabel', "Value"))
        n_runs = len(runs)
        n_data = yvals.size
        n_amps = int(n_data / n_runs)

        xvals = np.linspace(0, n_data-1, n_data)

        if yerrs is None:
            ax.plot(xvals, yvals, 'b.', **kwcopy)
        else:
            ax.errorbar(xvals, yvals, yerr=yerrs, fmt='b.', **kwcopy)

        locs = [n_amps//2 + i*n_amps for i in range(n_runs)]
        ax.set_xticks(locs)
        ax.set_xticklabels(runs, rotation=90)
        fig.tight_layout()

        o_dict = dict(fig=fig, ax=ax)
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
        if basename is None:
            plt.ion()
            plt.show()
            return

        for key, val in self._fig_dict.items():
            fig = val['fig']
            fig.savefig("%s_%s.png" % (basename, key))
            plt.close(fig)
