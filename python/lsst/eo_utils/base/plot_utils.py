"""Functions to help make plots and collect figures"""

import sys

import numpy as np

import astropy.visualization as viz
from astropy.visualization.mpl_normalize import ImageNormalize

from lsst.eotest.raft import RaftMosaic

from lsst.eotest.sensor import MaskedCCD, parse_geom_kwd

import lsst.afw.image as afwImage

from .config_utils import pop_values

from .image_utils import get_raw_image, raw_amp_image,\
    get_amp_list, unbias_amp, get_geom_regions,\
    get_image_frames_2d, unbiased_ccd_image_dict, get_amp_offset

from .defaults import TESTCOLORMAP

from . import mpl_utils

from matplotlib import ticker, colors
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1.inset_locator import inset_axes

mpl_utils.set_plt_ioff()



class FigureDict:
    """Object to make and collect figures.

    This is implemented as a dictionary of dictionaries,

    Each value is a dictionary with `matplotlib` objects for each figure
    """
    def __init__(self):
        """C'tor"""
        self._fig_dict = {}

    def add_figure(self, key, fig):
        """Added a figure

        Parameters
        ----------
        key : `str`
            Name of the figure
        fig : `matplotlib.figure.Figure`
            The figure we are adding
        """
        self._fig_dict[key] = dict(fig=fig)

    def get_figure(self, key):
        """Return a `Figure` by name"""
        return self._fig_dict[key]['fig']

    def keys(self):
        """Return the names of the figures"""
        return self._fig_dict.keys()

    def values(self):
        """Returns the sub-dictionary of `matplotlib` objects"""
        return self._fig_dict.values()

    def items(self):
        """Return the name : sub-dictionary pairs"""
        return self._fig_dict.items()

    def __getitem__(self, key):
        """Return a particular sub-dictionary by name"""
        return self._fig_dict[key]

    def get_obj(self, key, key2):
        """Return some other `matplotlib` object besides a `Figure`

        Parameters
        ----------
        key : `str`
            Key for the figure
        key2 : `str`
            Key for the object

        Returns
        -------
        retval : `object`
            Requested object
        """
        return self._fig_dict[key][key2]


    def get_amp_axes(self, key, iamp):
        """Return the `matplotlib` axes object for a particular amp

        Parameters
        ----------
        key : `str`
            Key for the figure.
        iamp : `int`
            Amplifier index

        Returns
        -------
        retval : `Axes`
            Requested `matplotlib` axes object
        """
        return self._fig_dict[key]['axs'].flat[iamp]


    def setup_figure(self, key, **kwargs):
        """Set up a figure with requested labeling

        Parameters
        ----------
        key : str
            Key for the figure.

        Keywords
        --------
        title : `str`
            Figure title
        xlabel : `str`
            X-axis label
        ylabel : `str`
            Y-axis label
        figsize : `tuple`
            Figure width, height in inches

        Returns
        -------
        fig : `Figure`
            The newly created `Figure`
        axes : `AxesSubplot`
            The axes objects
        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', None)
        ylabel = kwargs.get('ylabel', None)
        figsize = kwargs.get('figsize', (15, 10))

        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        if title is not None:
            fig.suptitle(title)
        if xlabel is not None:
            axes.set_xlabel(xlabel)
        if ylabel is not None:
            axes.set_ylabel(ylabel)

        o_dict = dict(fig=fig, axes=axes)
        self._fig_dict[key] = o_dict
        return o_dict


    def setup_amp_plots_grid(self, key, **kwargs):
        """Set up a 4x4 grid of plots with requested labeling

        Parameters
        ----------
        key : str
            Key for the figure.

        Keywords
        --------
        title : `str`
            Figure title
        xlabel : `str`
            X-axis label
        ylabel : `str`
            Y-axis label
        figsize : `tuple`
            Figure width, height in inches
        ymin : `float` or `None`
            Y-axis minimum value
        ymax : `float` or `None`
            Y-axis maximum value

        Returns
        -------
        fig : `Figure`
            The newly created `Figure`
        axes : `AxesSubplot`
            The axes objects
        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', None)
        ylabel = kwargs.get('ylabel', None)
        ymin = kwargs.get('ymin', None)
        ymax = kwargs.get('ymax', None)

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

        if ymin is not None or ymax is not None:
            for i_row in range(fig_nrow):
                for i_col in range(fig_ncol):
                    axs[i_row, i_col].set_ylim(ymin, ymax)

        o_dict = dict(fig=fig, axs=axs)
        self._fig_dict[key] = o_dict
        return o_dict


    def setup_amp_resid_plots_grid(self, key, **kwargs):
        """Set up a 4x4 grid of plots with requested labeling

        Parameters
        ----------
        key : str
            Key for the figure.

        Keywords
        --------
        title : `str`
            Figure title
        xlabel : `str`
            X-axis label
        ylabel : `str`
            Y-axis label
        ylabel_resid : `str`
            Y-axis residual label
        figsize : `tuple`
            Figure width, height in inches
        ymin : `float` or `None`
            Y-axis minimum value
        ymax : `float` or `None`
            Y-axis maximum value
        xscale : `str` or `None
            X-axis scaling
        tscale : `str` or `None
            Y-axis scaling

        Returns
        -------
        fig : `Figure`
            The newly created `Figure`
        axes : `AxesSubplot`
            The axes objects for the subplotsw
        body_axes : `list` of `Axes`
            The axes objects for the main plots
        resid_axes ; `list` of `Axes`
            The axes objects for the residual plots
        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', None)
        ylabel = kwargs.get('ylabel', None)
        ylabel_resid = kwargs.get('ylabel_resid', None)
        xmin = kwargs.get('xmin', None)
        xmax = kwargs.get('xmax', None)
        ymin = kwargs.get('ymin', None)
        ymax = kwargs.get('ymax', None)
        ymin_resid = kwargs.get('ymin_resid', None)
        ymax_resid = kwargs.get('ymax_resid', None)
        xscale = kwargs.get('xscale', None)
        yscale = kwargs.get('yscale', None)

        figsize = kwargs.get('figsize', (15, 10))

        fig_nrow = 4
        fig_ncol = 4
        fig, axs = plt.subplots(nrows=fig_nrow, ncols=fig_ncol, figsize=figsize)

        if title is not None:
            fig.suptitle(title)

        body_axes_list = []
        resid_axes_list = []
  
        for i_row in range(4):
            for i_col in range(4):
                axes = axs[i_row, i_col]
                axes.tick_params(labelleft=False, labelbottom=False)
                axes.set_visible(False)
                
                axes_body = inset_axes(axes, '100%', '60%', loc='upper right')
                axes_resid = inset_axes(axes, '100%', '30%', loc='lower right')

                if xscale is not None:
                    axes_body.set_xscale(xscale)
                    axes_resid.set_xscale(xscale)
                if yscale is not None:
                    axes_body.set_yscale(yscale)
                
                if ymin is not None or ymax is not None:                    
                    axes_body.set_ylim(ymin, ymax)
                if ymin_resid is not None or ymax_resid is not None:                    
                    axes_resid.set_ylim(ymin_resid, ymax_resid)

                if xmin is not None or xmax is not None:                    
                    axes_body.set_xlim(xmin, xmax)
                    axes_resid.set_xlim(xmin, xmax)

                if i_col == 0:
                    if ylabel is not None:
                        axes_body.set_ylabel(ylabel)
                    if ylabel_resid is not None:                    
                        axes_resid.set_ylabel(ylabel_resid)
                else:
                    axes_body.set_yticklabels([])
                    axes_resid.set_yticklabels([])
                axes_body.set_xticklabels([])
     
                if i_row == 3:
                    if xlabel is not None:
                        axes_resid.set_xlabel(xlabel)
                    else:
                        axes_resid.set_xticklabels([])
                
                body_axes_list.append(axes_body)
                resid_axes_list.append(axes_resid)

        o_dict = dict(fig=fig, axs=axs, body_axes=body_axes_list, resid_axes=resid_axes_list)
        self._fig_dict[key] = o_dict
        return o_dict


    def setup_region_plots_grid(self, key, **kwargs):
        """Set up a 2x3 grid of plots with requested labeling

        Parameters
        ----------
        key : str
            Key for the figure.

        Keywords
        --------
        title : `str`
            Figure title
        xlabel : `str`
            X-axis label
        ylabel : `str`
            Y-axis label
        figsize : `tuple`
            Figure width, height in inches
        ymin : `float` or `None`
            Y-axis minimum value
        ymax : `float` or `None`
            Y-axis maximum value

        Returns
        -------
        fig : `Figure`
            The newly created `Figure`
        axes : `AxesSubplot`
            The axes objects
        """
        title = kwargs.get('title', None)
        xlabel = kwargs.get('xlabel', "")
        ylabel = kwargs.get('ylabel', "")
        figsize = kwargs.get('figsize', (15, 10))

        regions = [" Imaging", " Serial", " Parallel"]
        directions = [" Row", " Column"]
        fig_nrow = len(regions)
        fig_ncol = len(directions)
        fig, axs = plt.subplots(nrows=fig_nrow, ncols=fig_ncol, figsize=figsize)

        if title is not None:
            fig.suptitle(title)

        for i_row, region in enumerate(regions):
            ax_row = axs[i_row, 0]
            ax_row.set_ylabel(ylabel + region)

        for i_col, direction in enumerate(directions):
            ax_col = axs[fig_nrow-1, i_col]
            ax_col.set_xlabel(xlabel + direction)

        o_dict = dict(fig=fig, axs=axs)
        self._fig_dict[key] = o_dict
        return o_dict


    def setup_raft_plots_grid(self, key, **kwargs):
        """Set up a 3x3 grid of plots with requested labeling
        Parameters
        ----------
        key : str
            Key for the figure.

        Keywords
        --------
        title : `str`
            Figure title
        xlabel : `str`
            X-axis label
        ylabel : `str`
            Y-axis label
        figsize : `tuple`
            Figure width, height in inches
        ymin : `float` or `None`
            Y-axis minimum value
        ymax : `float` or `None`
            Y-axis maximum value

        Returns
        -------
        fig : `Figure`
            The newly created `Figure`
        axes : `AxesSubplot`
            The axes objects
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

        Parameters
        ----------
        key : `str`
            Key for the figure.
        iamp : `int`
            Amp index
        freqs : `numpy.ndarray`
            The frequencies to be ploted on the x-axis
        fftpow : `numpy.ndarray`
            The power corresponding to the frequencies
        """
        n_row = len(fftpow)
        axes = self._fig_dict[key]['axs'].flat[iamp]
        axes.plot(freqs[0:int(n_row/2)], fftpow[0:int(n_row/2)])

    def plot_hist(self, key, iamp, data, **kwargs):
        """Histograms data and plots it

        Parameters
        ----------
        key : `str`
            Key for the figure.
        iamp : `int`
            Amp index
        data : `numpy.ndarray`
            Data to histogram

        Keywords
        --------
        xmin : `float`
            The binning minimum
        xmax : `float`
            The binning maximum
        nbins : `int`
            The number of bins to use
        """
        xmin = kwargs.get('xmin', None)
        xmax = kwargs.get('xmax', None)
        if xmin is not None and xmax is not None:
            xra = (xmin, xmax)
        else:
            xra = None

        hist = np.histogram(data, bins=kwargs['nbins'], range=xra)
        bins = (hist[1][0:-1] + hist[1][1:])/2.
        axes = self._fig_dict[key]['axs'].flat[iamp]
        axes.plot(bins, hist[0])

    def plot(self, key, iamp, xdata, ydata, **kwargs):
        """Plot x versus y data for one amp

        Parameters
        ----------
        key : `str`
            Key for the figure.
        iamp : `int`
            Amp index
        xdata : `numpy.ndarray`
            X-axis data
        ydata : `numpy.ndarray`
            Y-axis data
        kwargs
            Passed to matplotlib
        """
        kwcopy = kwargs.copy()
        ymin = kwcopy.pop('ymin', None)
        ymax = kwcopy.pop('ymax', None)
        axs = self._fig_dict[key]['axs'].flat[iamp]
        axs.plot(xdata, ydata, **kwcopy)
        if ymin is not None and ymax is not None:
            axs.set_ylim(ymin, ymax)


    def plot_resid(self, key, iamp, data_struct, **kwargs):
        """Plot x versus y data for one amp

        Parameters
        ----------
        key : `str`
            Key for the figure.
        iamp : `int`
            Amp index
        data_struct : `dict`
            Dictionary with x, y and model data
        kwargs
            Passed to matplotlib
        """
        kwcopy = kwargs.copy()
        ymin = kwcopy.pop('ymin', None)
        ymax = kwcopy.pop('ymax', None)
        axes_body = self._fig_dict[key]['body_axes'][iamp]
        axes_resid = self._fig_dict[key]['resid_axes'][iamp]
        
        xvals = data_struct['xvals']
        yvals = data_struct['yvals']
        resid_vals = data_struct['resid_vals']
        model_vals = data_struct.get('model_vals', None)
        resid_errors = data_struct.get('resid_errors', None)
        body_mask = data_struct.get('mask', None)
        resid_mask = data_struct.get('resid_mask', None)

        if body_mask is None:
            body_mask = np.ones(xvals.shape, bool)
        if resid_mask is None:
            resid_mask = np.ones(xvals.shape, bool)
        axes_body.plot(xvals[body_mask], yvals[body_mask], '.')
        if model_vals is not None:
            axes_body.plot(xvals[body_mask], model_vals[body_mask], 'r--')
        
        if resid_errors is None:
            axes_resid.plot(xvals[resid_mask], resid_vals[resid_mask], '.')
        else:
            axes_resid.errorbar(xvals[resid_mask], resid_vals[resid_mask],
                                yerr=resid_errors[resid_mask], fmt='.')


    def plot_stats_band_amp(self, key, iamp, xvals, **kwargs):
        """Plot the data each amp in a set of runs in a single chart

        Parameters
        ----------
        key : `str`
            Key for the figure.
        iamp : `int`
            Amp index
        xvals : `numpy.ndarray`
            X-axis data

        Keywords
        --------
        means : `array`
            Means of the y-axis values
        stds : `array`
            Standard deviations of the y-axis values
        mins : `array`
            Minimum y-axis values
        maxs : `array`
            Maximum y-axis values
        """
        means = kwargs.pop('means')
        stds = kwargs.pop('stds')

        axes = self._fig_dict[key]['axs'].flat[iamp]
        axes.fill_between(xvals, kwargs.pop('mins'), kwargs.pop('maxs'), color='green')
        axes.fill_between(xvals, means-stds, means+stds, color='yellow')
        axes.plot(xvals, kwargs.pop('medians'), '.')


    def plot_single(self, key, xdata, ydata, **kwargs):
        """Plot x versus y data in a single figure

        Parameters
        ----------
        key : `str`
            Key for the figure.
        xdata : `numpy.ndarray`
            X-axis data
        ydata : `numpy.ndarray`
            Y-axis data
        kwargs
            Passed to matplotlib
        """
        self._fig_dict[key]['axes'].plot(xdata, ydata, **kwargs)


    def plot_two_image_hist2d(self, key, iamp, img_x, img_y, **kwargs):
        """Plot pixel-py-pixel scatter plot for two images

        Parameters
        ----------
        key : `str`
            Key for the figure.
        iamp : `int`
            Amp index
        img_x : `numpy.ndarray`
            X-axis data
        img_y : `numpy.ndarray`
            Y-axis data
        kwargs
            Passed to `matplotlib`
        """
        histrange = kwargs.get('range', None)

        img_x_flat = img_x.flatten()
        img_y_flat = img_y.flatten()

        axs = self.get_amp_axes(key, iamp)

        if histrange is not None:
            img_x_flat = img_x_flat.clip(histrange[0][0], histrange[0][1])
            img_y_flat = img_y_flat.clip(histrange[1][0], histrange[1][1])

        axs.hist2d(img_x_flat, img_y_flat, norm=colors.LogNorm(), **kwargs)


    def plot_xy_axs_from_tabledict(self, dtables, key, idx, plotkey, **kwargs):
        """Plot x versus y data for each sub-figure using data in a table

        Parameters
        ----------
        dtables : `TableDict`
            Data tables from the analysis
        key : `str`
            Key for the data for this plot
        idx : `int`
            Axis index for this plot
        plotkey : `str`
            Key for the plot

        Keywords
        --------
        x_name : `str`
            Column name for the x-axis data
        y_name : `str`
            Start of the name for the y-axis data
        ymin : `float`
            Y-axis min
        ymax : `float`
            Y-axis max
        """
        kwcopy = kwargs.copy()
        x_name = kwcopy.pop('x_name', 'x')
        y_name = kwcopy.pop('y_name', 'y')

        file_data = dtables['files']
        dtab = dtables[key]
        xcol = dtab[x_name]
        for col in dtab.columns:
            if col.find(y_name) != 0:
                continue
            valarray = dtab[col]
            for row, test_type in zip(valarray.T, file_data['testtype']):
                print(y_name, row.max())
                self.plot(plotkey, idx, xcol, row,
                          color=TESTCOLORMAP.get(test_type, 'gray'),
                          **kwcopy)


    def plot_xy_from_tabledict(self, dtables, key, plotkey, **kwargs):
        """Plot x versus y data for each column in a table on a single plot

        Parameters
        ----------
        dtables : `TableDict`
            Data tables from the analysis
        key : `str`
            Key for the data for this plot
        plotkey : `str`
            Key for the plot

        Keywords
        --------
        x_name : `str`
            Column name for the x-axis data
        y_name : `str`
            Start of the name for the y-axis data
        ymin : `float`
            Y-axis min
        ymax : `float`
            Y-axis max
        """
        x_name = kwargs.get('x_name', 'x')
        y_name = kwargs.get('y_name', 'y')
        ymin = kwargs.get('ymin', -np.inf)
        ymax = kwargs.get('ymax', np.inf)

        dtab = dtables.get_table(key)
        xcol = dtab[x_name]
        for col in dtab.columns:
            if col.find(y_name) != 0:
                continue
            self.plot_single(plotkey, xcol, dtab[col].clip(ymin, ymax))


    def plot_xy_amps_from_tabledict(self, dtables, key, plotkey, **kwargs):
        """Plot x versus y data for each column in a table for each sub-plot

        Parameters
        ----------
        dtables : `TableDict`
            Data tables from the analysis
        key : `str`
            Key for the data for this plot
        plotkey : `str`
            Key for the plot

        Keywords
        --------
        x_name : `str`
            Column name for the x-axis data
        y_name : `str`
            Start of the name for the y-axis data
        ymin : `float`
            Y-axis min
        ymax : `float`
            Y-axis max
        """
        kwcopy = kwargs.copy()
        x_name = kwcopy.pop('x_name', 'x')
        y_name = kwcopy.pop('y_name', 'y')

        file_data = dtables['files']
        dtab = dtables[key]
        xcol = dtab[x_name]
        for col in dtab.columns:
            if col.find(y_name) != 0:
                continue
            amp = int(col.split('_')[-1][1:])
            valarray = dtab[col]
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

                self.plot(plotkey, amp, xcol, row, color=color, **kwcopy)


    def plot_raft_correl_matrix(self, key, data, **kwargs):
        """Plot a correlation matrix

        Parameters
        ----------
        key : `str`
            Key for the figure.
        data : `numpy.ndarray`
            Data to histogram

        Keywords
        --------
        slots : `list`
            Names of the slots
        title : `str`
            Title for the figure
        figsize : `tuple`
            Figure width, height in inches
        vmin : `float`
            minimum value for color axis
        vmax : `float`
            maximum value for color axis

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
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
        axes = fig.add_subplot(111)

        if title is not None:
            axes.set_title(title)

        norm = ImageNormalize(vmin=vrange[0], vmax=vrange[1])
        img = axes.imshow(data, interpolation='none', norm=norm)
        cbar = plt.colorbar(img)

        if slots is not None:
            amps = 16
            major_locs = [i*amps - 0.5 for i in range(len(slots) + 1)]
            minor_locs = [amps//2 + i*amps for i in range(len(slots))]
            for axis in (axes.xaxis, axes.yaxis):
                axis.set_tick_params(which='minor', length=0)
                axis.set_major_locator(ticker.FixedLocator(major_locs))
                axis.set_major_formatter(ticker.FixedFormatter(['']*len(major_locs)))
                axis.set_minor_locator(ticker.FixedLocator(minor_locs))
                axis.set_minor_formatter(ticker.FixedFormatter(slots))

        o_dict = dict(fig=fig, axes=axes, img=img, cbar=cbar)
        self._fig_dict[key] = o_dict
        return o_dict

    def plot_raft_amp_values(self, key, data, **kwargs):
        """Make a 2D color image of an array of data

        Parameters
        ----------
        key : `str`
            Key for the figure.
        data : `numpy.ndarray`
            Data to plot

        Keywords
        --------
        title : `str`
            Title for the figure
        figsize : `tuple`
            Figure width, height in inches
        xlabel : `str`
            X-axis label
        ylabel : `str`
            Y-axis label
        ymin : `float`
            Minimum value for y axis
        ymax : `float`
            Maximum value for y axis
        yerrs : `array` or `None`
            Y-axis errors, if available

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        kwcopy = kwargs.copy()
        kwsetup = pop_values(kwcopy, ['title', 'xlabel', 'ylabel', 'figsize'])

        o_dict = self.setup_figure(key, **kwsetup)
        axes = o_dict['axes']
        slots = kwcopy.pop('slots', None)
        ymin = kwcopy.pop('ymin', None)
        ymax = kwcopy.pop('ymax', None)
        yerrs = kwcopy.pop('yerrs', None)
        if ymin is not None and ymax is not None:
            axes.set_ylim(ymin, ymax)
        nvals = len(data)
        xvals = np.linspace(0., nvals-1, nvals)
        if yerrs is None:
            axes.plot(xvals, data, 'b.', **kwcopy)
        else:
            axes.errorbar(xvals, data, yerr=yerrs, fmt='b.', **kwcopy)
        if slots is not None:
            amps = 16
            major_locs = [i*amps - 0.5 for i in range(len(slots) + 1)]
            minor_locs = [amps//2 + i*amps for i in range(len(slots))]
            for axis in [axes.xaxis]:
                axis.set_tick_params(which='minor', length=0)
                axis.set_major_locator(ticker.FixedLocator(major_locs))
                axis.set_major_formatter(ticker.FixedFormatter(['']*len(major_locs)))
                axis.set_minor_locator(ticker.FixedLocator(minor_locs))
                axis.set_minor_formatter(ticker.FixedFormatter(slots))




    def plot_stat_color(self, key, data, **kwargs):
        """Make a 2D color image of an array of data

        Parameters
        ----------
        key : `str`
            Key for the figure.
        data : `numpy.ndarray`
            Data to plot

        Keywords
        --------
        title : `str`
            Title for the figure
        clabel : `str`
            Label for the colorbar
        figsize : `tuple`
            Figure width, height in inches
        vmin : `float`
            minimum value for color axis
        vmax : `float`
            maximum value for color axis

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        kwcopy = kwargs.copy()
        title = kwcopy.pop('title', None)
        clabel = kwcopy.pop('clabel', None)
        figsize = kwcopy.pop('figsize', (14, 8))
        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        axes.set_xlabel(kwcopy.pop('xlabel', "Amp. Index"))
        axes.set_ylabel(kwcopy.pop('ylabel', "Slot Index"))
        img = axes.imshow(data, interpolation='nearest', **kwcopy)
        if title is not None:
            axes.set_title(title)
        cbar = fig.colorbar(img, ax=axes)
        if clabel is not None:
            cbar.ax.set_ylabel(clabel, rotation=-90, va='bottom')
        o_dict = dict(fig=fig, axes=axes, img=img, cbar=cbar)
        self._fig_dict[key] = o_dict
        return o_dict


    def plot_raft_vals_from_table(self, dtable, plotkey, **kwargs):
        """Plot x versus y data for each sub-figure using data in a table

        Parameters
        ----------
        dtable : `Table`
            Data table
        plotkey : `str`
            Key for the plot

        Keywords
        --------
        y_name : `str`
            Column name for the y-axis data
        ymin : `float`
            Y-axis min
        ymax : `float`
            Y-axis max

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        kwcopy = kwargs.copy()

        kwsetup = pop_values(kwcopy, ['title', 'xlabel', 'ylabel', 'figsize', 'ymin', 'ymax'])

        o_dict = self.setup_raft_plots_grid(plotkey, **kwsetup)
        axs = o_dict['axs']

        slots = dtable['slot']
        amps = dtable['amp']
        val_array = dtable[kwcopy.pop('y_name')]
        nxvals = val_array.shape[1]
        xvals = np.linspace(0, nxvals-1, nxvals)
        for slot, amp, vals in zip(slots, amps, val_array):
            axes = axs.flat[slot]
            axes.plot(xvals, vals, label="amp%02i" % (amp+1), **kwcopy)
        return o_dict

    def plot_amp_arrays(self, key, array_dict, **kwargs):
        """Plot the data from all 16 amps on a sensor in a single figure

        Parameters
        ----------
        key : `str`
            Key for the plot
        array_dict : `dict`
            Dictionary of data for each amp

        Keywords
        --------
        ymin : `float`
            Y-axis min
        ymax : `float`
            Y-axis max

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        fig, axs = plt.subplots(2, 8, figsize=(15, 10))
        axs = axs.ravel()

        for idx, (_, darray) in enumerate(sorted(array_dict)):
            axs[idx].imshow(darray, origin='low', interpolation='none', **kwargs)
            axs[idx].set_title('Amp {}'.format(idx + 1))

        plt.tight_layout()
        o_dict = dict(fig=fig, axs=axs)
        self._fig_dict[key] = o_dict
        return o_dict


    def plot_sensor(self, key, ccd, **kwargs):
        """Plot the data from all 16 amps on a sensor in a single figure

        Parameters
        ----------
        key : `str`
            Key for the figure.
        ccd : `MaskedCCD` or `MaskedImage`
            Object with the image data

        Keywords
        --------
        vmin : `float`
            minimum value for color axes
        vmax : `float`
            maximum value for color axes
        bias : `str` or `None`
            method used to subtract bias
        superbias_frame : `MaskedCCD` or `None`
            Superbias image to subtract
        subtract_mean : `bool`
            Flag to subtract mean value from each image

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        vmin = kwargs.get('vmin', -10)
        vmax = kwargs.get('vmax', 10)
        bias_type = kwargs.get('bias', None)
        superbias_frame = kwargs.get('superbias_frame', None)
        subtract_mean = kwargs.get('subtract_mean', False)

        fig, axs = plt.subplots(2, 8, figsize=(15, 10))
        axs = axs.ravel()

        unbiased_images = unbiased_ccd_image_dict(ccd,
                                                  superbias_frame=superbias_frame,
                                                  bias_type=bias_type)
        amps = get_amp_list(ccd)
        for idx, amp in enumerate(amps):
            image = unbiased_images[amp]
            darray = image.image.array
            if subtract_mean:
                darray -= darray.mean()

            axs[idx].imshow(darray, origin='low', interpolation='none', vmin=vmin, vmax=vmax)
            axs[idx].set_title('Amp {}'.format(amp))

        plt.tight_layout()
        o_dict = dict(fig=fig, axs=axs)
        self._fig_dict[key] = o_dict
        return o_dict


    def histogram_array(self, key, ccd, **kwargs):
        """Plot the data from all 16 amps on a sensor in a single figure

        Parameters
        ----------
        key : `str`
            Key for the figure.
        ccd : `MaskedCCD` or `AFWImage`
            Object with the image data

        Keywords
        --------
        vmin : `float`
            minimum value for color axes
        vmax : `float`
            maximum value for color axes
        bias : `str` or `None`
            method used to subtract bias
        superbias_frame : `MaskedCCD` or `None`
            Superbias image to subtract
        subtract_mean : `bool`
            Flag to subtract mean value from each image

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        kwcopy = kwargs.copy()

        kwsetup = pop_values(kwcopy, ['title', 'xlabel', 'ylabel', 'figsize'])
        o_dict = self.setup_amp_plots_grid(key, **kwsetup)

        axs = o_dict['axs']
        unbiased_images = unbiased_ccd_image_dict(ccd, **kwcopy)

        hist_range = kwcopy.pop('range')

        for amp, image in unbiased_images.items():
            regions = get_geom_regions(ccd, amp)
            frames = get_image_frames_2d(image, regions)
            darray = frames[kwcopy.pop('region', 'imaging')]
            if kwcopy.pop('subtract_mean', False):
                darray -= darray.mean()
            if hist_range is None:
                hist_range = (darray.min(), darray.max())
            if isinstance(ccd, MaskedCCD):
                idx = amp - 1
            else:
                idx = amp
            axes = axs.flat[idx]
            axes.hist(darray.flat, range=hist_range, **kwcopy)

        plt.tight_layout()

        self._fig_dict[key] = o_dict
        return o_dict


    def histogram_raft_array(self, key, array_dict, **kwargs):
        """Plot the data from all the slots of raft

        Parameters
        ----------
        key : `str`
            Key for the figure.
        array_dict : `dict`
            Dictionary keyed by slot data for each slot
        kwargs
            Passed to matplotlib

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        kwcopy = kwargs.copy()

        kwsetup = pop_values(kwcopy, ['title', 'xlabel', 'ylabel', 'figsize'])

        o_dict = self.setup_raft_plots_grid(key, **kwsetup)

        axs = o_dict['axs']
        for islot, (slot, slot_data) in enumerate(array_dict.items()):

            axes = axs.flat[islot]

            for idx in range(16):

                darray = slot_data[idx]

                if kwargs.pop('subtract_mean', False):
                    darray -= darray.mean()

                try:
                    axes.hist(darray.flat, label="amp%02i" % (idx+1), **kwcopy)
                except ValueError:
                    sys.stderr.write("Plotting failed for %s %i\n" % (slot, idx))

        plt.tight_layout()

        self._fig_dict[key] = o_dict
        return o_dict


    def plot_run_chart(self, key, runs, yvals, **kwargs):
        """Plot the data each amp in a set of runs in a single chart

        Parameters
        ----------
        key : `str`
            Key for the figure.
        runs : `array`
            Aray of the run info
        yvals : `list`
            Values being plotted
        kwargs
            Passed to `matplotlib`

        Keywords
        --------
        title : `str`
            Figure title
        figsize : `tuple`
            Figure width, height in inches
        ylabel : `str`
            y-axis label
        yextras : `list`
            Additional quantities to plot on y-axis

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        kwcopy = kwargs.copy()
        yerrs = kwcopy.pop('yerrs', None)
        title = kwcopy.pop('title', None)
        yextras = kwcopy.pop('yextras', None)
        fig = plt.figure(figsize=kwcopy.pop('figsize', (14, 8)))
        axes = fig.add_subplot(111)


        if title is not None:
            axes.set_title(title)

        axes.set_ylabel(kwcopy.pop('ylabel', "Value"))
        n_runs = len(runs)
        n_data = yvals.size
        n_amps = int(n_data / n_runs)

        xvals = np.linspace(0, n_data-1, n_data)

        if yerrs is None:
            axes.plot(xvals, yvals, 'b.', **kwcopy)
        else:
            axes.errorbar(xvals, yvals, yerr=yerrs, fmt='b.', **kwcopy)

        if yextras is not None:
            for yextra in yextras:
                axes.plot(xvals, yextra, '.', **kwcopy)

        locs = [n_amps//2 + i*n_amps for i in range(n_runs)]
        axes.set_xticks(locs)
        axes.set_xticklabels(runs, rotation=90)
        fig.tight_layout()

        o_dict = dict(fig=fig, axes=axes)
        self._fig_dict[key] = o_dict
        return o_dict


    def plot_ccd_mosaic(self, key, ccd, **kwargs):
        """Combine amplifier image arrays into a single mosaic CCD image image

        Parameters
        ----------
        key : `str`
            Key for the figure.
        ccd : `MaskedCCD`
            The CCD we are plotting

        Keywords
        --------
        bias : `str` or `None`
            Method to subtract overscan
        superbias_frame : `MaskedCCD` or `None`
            Superbias image
        gains : `array` or `None`
            Gain values
        figsize : `tuple`
            Figure size (in inches)

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object
        """
        kwcopy = kwargs.copy()
        bias_type = kwcopy.pop('bias', None)
        superbias_frame = kwcopy.pop('superbias_frame', None)
        gains = kwcopy.pop('gains', None)
        figsize = kwcopy.pop('figsize', (10, 10))
        vmin = kwcopy.pop('vmin', None)
        vmax = kwcopy.get('vmax', None)

        datasec = parse_geom_kwd(ccd.amp_geom[1]['DATASEC'])
        nx_segments = 8
        ny_segments = 2
        nx_pix = nx_segments*(datasec['xmax'] - datasec['xmin'] + 1)
        ny_pix = ny_segments*(datasec['ymax'] - datasec['ymin'] + 1)

        # this array has [0,0] in the upper right corner on LCA-13381 view of CCDs
        # and [ny,nx] in the lower right
        mosaic = np.zeros((ny_pix, nx_pix), dtype=np.float32)

        offset = get_amp_offset(ccd, superbias_frame)

        for ypos in range(ny_segments):
            for xpos in range(nx_segments):
                amp = ypos*nx_segments + xpos + 1
                regions = get_geom_regions(ccd, amp)
                serial_oscan = regions['serial_overscan']
                imaging = regions['imaging']

                detsec = parse_geom_kwd(ccd.amp_geom[amp]['DETSEC'])
                xmin = nx_pix - max(detsec['xmin'], detsec['xmax'])
                xmax = nx_pix - min(detsec['xmin'], detsec['xmax']) + 1
                ymin = ny_pix - max(detsec['ymin'], detsec['ymax'])
                ymax = ny_pix - min(detsec['ymin'], detsec['ymax']) + 1
                #
                # Extract bias-subtracted image for this segment - overscan corrected here
                #
                superbias_im = raw_amp_image(superbias_frame, amp + offset)
                img = get_raw_image(ccd, amp)
                segment_image = unbias_amp(img, serial_oscan,
                                           bias_type=bias_type, superbias_im=superbias_im)
                subarr = segment_image[imaging].array
                #
                # Determine flips in x- and y- direction
                #
                if detsec['xmax'] > detsec['xmin']: # flip in x-direction
                    subarr = subarr[:, ::-1]
                if detsec['ymax'] > detsec['ymin']: # flip in y-direction
                    subarr = subarr[::-1, :]
                #
                # Convert from ADU to e-
                #
                if gains is not None:
                    subarr *= gains[amp]
                #
                # Set sub-array to the mosaiced image
                #
                mosaic[ymin:ymax, xmin:xmax] = subarr

        # transpose and rotate by -90 to get a mosaic ndarray that will
        # look like the LCA-13381 view with matplotlib(origin='lower') rotated CW by 90 for DM view
        mosaicprime = np.zeros((ny_pix, nx_pix), dtype=np.float32)
        mosaicprime[:, :] = np.rot90(np.transpose(mosaic), k=-1)

        if vmin is None or vmax is None:
            interval = viz.PercentileInterval(98.)
            vrange = interval.get_limits(mosaicprime.flatten())
        else:
            vrange = (vmin, vmax)
        norm = ImageNormalize(vmin=vrange[0], vmax=vrange[1])

        image = afwImage.ImageF(mosaicprime)

        fig, axes = plt.subplots(nrows=1, ncols=1, figsize=figsize)
        axes.set_xlabel(kwcopy.pop('xlabel', "X [pix]"))
        axes.set_ylabel(kwcopy.pop('ylabel', "Y [pix]"))
        img = axes.imshow(image.array, interpolation='nearest', origin='lower', norm=norm, **kwcopy)
        cbar = plt.colorbar(img)

        plt.tight_layout()

        o_dict = dict(fig=fig, axes=axes, img=img, image=image, cbar=cbar)
        self._fig_dict[key] = o_dict
        return o_dict


    def plot_raft_mosaic(self, key, file_dict, **kwargs):
        """Make a mosaic of all the CCDs in a raft

        Parameters
        ----------
        key : `str`
            Key for the figure.
        file_dict : `dict`
            Image files, keyed by slot
        kwargs
            Passed to the RaftMosaic c'tor and plot() functions

        Returns
        -------
        o_dict : `dict`
            Dictionary of `matplotlib` object

        """
        kwcopy = kwargs.copy()
        kwctor = pop_values(kwcopy, ['gains',
                                     'bias_subtract',
                                     'bias_frames',
                                     'dark_currents',
                                     'segment_processor'])

        raft_mosaic = RaftMosaic(file_dict, **kwctor)
        fig = raft_mosaic.plot(**kwcopy)
        o_dict = dict(fig=fig)
        self._fig_dict[key] = o_dict
        return o_dict


    def make_raft_outlier_plots(self, dtable, prefix=""):
        """Make a set of plots of about the number of outlier pixels

        Parameters
        ----------
        dtable : `Table`
            Table with the outlier dataq
        prefix : `str`
            Prepended to the plot keys
        """
        self.plot_raft_vals_from_table(dtable, prefix + 'out_row',
                                       title='Outliers by row',
                                       y_name='row_data',
                                       xlabel='Row',
                                       ylabel='N bad pixels',
                                       ymin=0, ymax=50)
        self.plot_raft_vals_from_table(dtable, prefix + 'out_col',
                                       title='Outliers by col',
                                       y_name='col_data',
                                       xlabel='Row',
                                       ylabel='N bad pixels',
                                       ymin=0, ymax=50)
        self.plot_stat_color(prefix + 'nbad',
                             dtable['nbad_total'].reshape(9, 16).clip(0, 0.05),
                             title="Fraction of pixels")
        self.plot_stat_color(prefix + 'nbad_row',
                             dtable['nbad_rows'].reshape(9, 16).clip(0, 0.05),
                             title="Fraction of row with >= 10 outliers")
        self.plot_stat_color(prefix + 'nbad_col',
                             dtable['nbad_cols'].reshape(9, 16).clip(0, 0.05),
                             title="Fraction of cols with >= 10 outliers")

    def savefig(self, key, filename):
        """Save a single figure

        Parameters
        ----------
        key : `str`
            Key for the figure.
        filename : `str`
            Name of the output file
        """
        fig = self._fig_dict[key]['fig']
        fig.savefig(filename)
        plt.close(fig)

    def save_all(self, basename, ftype='png'):
        """Save all the figures

        The files will be named {basename}_{key}.png

        If basename is None then the file will be shown on the display and not saved

        Parameters
        ----------
        basename : `str` or `None`
            Base of the output file names
        ftype : `str`
            File type to same, also filename extension
        """
        if basename is None:
            plt.ion()
            plt.show()
            return

        for key, val in self._fig_dict.items():
            fig = val['fig']
            fig.savefig("%s_%s.%s" % (basename, key, ftype))
            plt.close(fig)
