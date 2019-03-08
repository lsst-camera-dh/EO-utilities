"""Functions to analyse bias and superbias frames"""

import os
import sys
import itertools

import numpy as np
from scipy import fftpack

import lsst.afw.math as afwMath
import lsst.eotest.image_utils as imutil

from .file_utils import get_bias_and_mask_files_run, get_hardware_type_and_id,\
    superbias_filename, superbias_stat_filename,\
    bias_plot_basename, superbias_plot_basename,\
    makedir_safe

from .butler_utils import getButler, get_bias_and_mask_files_butler

from .config_utils import DEFAULT_DB, DEFAULT_OUTDIR,\
    DEFAULT_STAT_TYPE, DEFAULT_BITPIX

from .plot_utils import FigureDict

from .image_utils import get_dims_from_ccd, get_readout_frequencies_from_ccd,\
    get_geom_regions, get_dimension_arrays_from_ccd,\
    get_raw_image, get_ccd_from_id, get_amp_list,\
    get_image_frames_2d,\
    array_struct, unbias_amp, make_superbias

from .iter_utils import EO_AnalyzeSlotTask, EO_AnalyzeRaftTask,\
    AnalysisIterator,\
    iterate_over_slots, iterate_over_rafts


DEFAULT_BIAS_TYPE = 'spline'
DEFAULT_SUPERBIAS_TYPE = None
SBIAS_TEMPLATE = 'superbias/templates/sbias_template.fits'

class BiasAnalysisBySlot(AnalysisIterator):
    """Small class to iterate an analysis task over all the slots in a raft"""
    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisIterator.__init__(self, EO_AnalyzeSlotTask(analysis_func), argnames)

    def call_func(self, run_num, **kwargs):
        """Call the analysis function for one run

        @param run_num (str)  The run identifier
        @param kwargs
            db (str)    The database to look for the data
            All the remaining keyword arguments are passed to the analysis function
        """
        htype, hid = get_hardware_type_and_id(kwargs.get('db', DEFAULT_DB), run_num)
        butler_repo = kwargs.get('butler_repo', None)
        kwargs['run_num'] = run_num
        if butler_repo is None:
            butler = None
            data_files = get_bias_and_mask_files_run(run_num, **kwargs)
        else:
            butler = getButler(butler_repo)
            data_files = get_bias_and_mask_files_butler(butler, run_num, **kwargs)
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            iterate_over_slots(self.task, butler, data_files, **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))


class BiasAnalysisByRaft(AnalysisIterator):
    """Small class to iterate an analysis task over all the raft and then all the slots in a raft"""
    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisIterator.__init__(self, EO_AnalyzeRaftTask(analysis_func), argnames)

    def call_func(self, run_num, **kwargs):
        """Call the analysis function for one run

        @param run_num (str)  The run identifier
        @param kwargs
            db (str)    The database to look for the data
            All the remaining keyword arguments are passed to the analysis function
        """
        htype, hid = get_hardware_type_and_id(kwargs.get('db', DEFAULT_DB), run_num)
        butler_repo = kwargs.get('butler_repo', None)
        if butler_repo is None:
            butler = None
            data_files = get_bias_and_mask_files_run(run_num, **kwargs)
        else:
            butler = getButler(butler_repo)
            data_files = get_bias_and_mask_files_butler(butler, run_num, **kwargs)

        kwargs['run_num'] = run_num
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            self.task.run(butler, data_files, **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))


def make_superbias_slot(butler, slot_data, **kwargs):
    """Make superbias frame for one slot

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        stat (str)           Statistic to use to stack data
        outdir (str)         Output directory
        bitpix (int)         Output data format BITPIX field
        skip (bool)          Flag to skip making superbias, only produce plots
        plot (bool)          Plot superbias images
        stats_hist (bool)    Plot superbias summary histograms
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)
    stat_type = kwargs.get('stat', DEFAULT_STAT_TYPE)
    #statistic = kwargs.get('statistic', afwMath.MEDIAN)
    #bitpix = kwargs.get('bitpix', DEFAULT_BITPIX)
    #skip = kwargs.get('skip', False)
    #plot = kwargs.get('plot', False)
    #stats_hist = kwargs.get('stats_hist', False)

    bias_files = slot_data['bias_files']
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files.\n" % (slot, len(bias_files)))

    if stat_type.upper() in afwMath.__dict__:
        statistic = afwMath.__dict__[stat_type.upper()]
    else:
        raise ValueError("Can not convert %s to a valid statistic to perform stacking" % stat_type)

    if statistic == afwMath.MEDIAN:
        output_file = superbias_filename(outdir, raft, run_num, slot, bias_type)
    else:
        output_file = superbias_stat_filename(outdir, raft, run_num, slot,
                                              stat_type=stat_type, bias_type=bias_type)

    makedir_safe(output_file)

    if not kwargs.get('skip', False):
        sbias = make_superbias(butler, bias_files,
                               statistic=statistic,
                               bias_type=bias_type)
        imutil.writeFits(sbias, output_file, SBIAS_TEMPLATE, kwargs.get('bitpix', DEFAULT_BITPIX))

    figs = FigureDict()

    if kwargs.get('plot', False):
        figs.plot_sensor("img", output_file, mask_files)

    if kwargs.get('stats_hist', False):
        figs.histogram_array("hist", output_file, mask_files,
                             title="Historam of RMS of bias-images, per pixel",
                             xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                             nbins=200, vmin=0., vmax=20.)

    figs.save_all(output_file.replace('.fits', ''))


def plot_bias_v_row_slot(butler, slot_data, **kwargs):
    """Plot the bias as function of row

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        outdir (str)         Output directory
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files'][0:5]
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i (mask %i) files: \n" % (slot, len(bias_files), len(mask_files)))

    figs = FigureDict()

    figs.setup_amp_plots_grid("val",
                              title="Bias by row",
                              xlabel="row",
                              ylabel="Magnitude [ADU]")

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)
        if ifile == 0:
            dims = get_dims_from_ccd(butler, ccd)
            xrow_s = np.linspace(0, dims['nrow_s']-1, dims['nrow_s'])

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            im = get_raw_image(butler, ccd, amp)
            bim = imutil.bias_image(im, serial_oscan, bias_method=bias_type)
            bim_row_mean = bim[serial_oscan].getArray().mean(1)
            figs.plot("val", i, xrow_s[0:len(bim_row_mean)], bim_row_mean)

    sys.stdout.write("!\n")
    sys.stdout.flush()

    output_file = bias_plot_basename(outdir, raft, run_num, slot,
                                     plotname='biasval', bias_type=bias_type)
    makedir_safe(output_file)

    figs.savefig("val", output_file)



def plot_bias_fft_slot(butler, slot_data, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files']
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    figs = FigureDict()

    figs.setup_amp_plots_grid("i_row", title="FFT of imaging region mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
    figs.setup_amp_plots_grid("s_row", title="FFT of serial overscan mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
    figs.setup_amp_plots_grid("p_row", title="FFT of parallel overscan mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")

    if superbias_type is None:
        superbias_frame = None
    else:
        superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
        superbias_frame = get_ccd_from_id(None, superbias_file, mask_files)


    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)
        if ifile == 0:
            freqs_dict = get_readout_frequencies_from_ccd(butler, ccd)

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

            for key in ['i', 's', 'p']:
                freqs = freqs_dict["freqs_%s" % key]
                struct = array_struct(frames['%s_array' % key], do_std=std)
                fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
                fftpow /= len(fftpow)/2
                figs.plot_fft('%s_row' % key, i, freqs, np.sqrt(fftpow))

    sys.stdout.write("!\n")
    sys.stdout.flush()

    outbase = bias_plot_basename(outdir, raft, run_num, slot,
                                 plotname="bias_fft", bias_type=bias_type, superbias_type=superbias_type)
    makedir_safe(outbase)
    figs.save_all(outbase)


def plot_bias_struct_slot(butler, slot_data, **kwargs):
    """Plot the row-wise and col-wise struture
    in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files'][0:5]
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()


    figs = FigureDict()
    region_keys = ['i', 's', 'p']
    region_labels = ['Imaging region', 'Serial overscan', 'Parallel overscan']

    for rkey, rlabel in zip(region_keys, region_labels):
        for dkey in ['row', 'col']:
            figs.setup_amp_plots_grid('%s_%s' % (rkey, dkey), title="%s, profile by %s" % (rlabel, dkey),
                                      xlabel=dkey, ylabel="ADU")

    if superbias_type is None:
        superbias_frame = None
    else:
        superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
        superbias_frame = get_ccd_from_id(None, superbias_file, mask_files)

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)
        if ifile == 0:
            dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)

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

            for key in ['i', 's', 'p']:
                xrow = dim_array_dict["row_%s" % key]
                xcol = dim_array_dict["col_%s" % key]
                struct = array_struct(frames['%s_array' % key], do_std=std)
                #print (key, xrow.shape, xcol.shape, struct['rows'].shape, struct['cols'].shape)
                figs.plot("%s_row" % key, i, xrow, struct['rows'])
                figs.plot("%s_col" % key, i, xcol, struct['cols'])

    sys.stdout.write("!\n")
    sys.stdout.flush()
    outbase = bias_plot_basename(outdir, raft, run_num, slot,
                                 plotname="bias", bias_type=bias_type, superbias_type=superbias_type)
    makedir_safe(outbase)

    if std:
        outbase += "_std"

    figs.save_all(outbase)


def plot_correl_wrt_oscan_slot(butler, slot_data, **kwargs):
    """Plot the correlations between the imaging section
    and the overscan regions in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        outdir (str)         Output directory
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files']
    mask_files = slot_data['mask_files']

    nfiles = len(bias_files)

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    figs = FigureDict()

    figs.setup_amp_plots_grid("row", title="Correlation: imaging region and serial overscan",
                              xlabel="Correlation",
                              ylabel="Number of frames")
    figs.setup_amp_plots_grid("col", title="Correlation: imaging region and paralell overscan",
                              xlabel="Correlation",
                              ylabel="Number of frames")

    ref_frames = {}

    s_correl = np.ndarray((16, nfiles-1))
    p_correl = np.ndarray((16, nfiles-1))

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)
        if ifile == 0:
            dims = get_dims_from_ccd(butler, ccd)
            nrow_i = dims['nrow_i']
            ncol_i = dims['ncol_i']

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):

            regions = get_geom_regions(butler, ccd, amp)
            image = get_raw_image(butler, ccd, amp)

            frames = get_image_frames_2d(image, regions)

            if ifile == 0:
                ref_frames[i] = frames
                continue

            ref_i_array = ref_frames[i]['i_array']
            ref_s_array = ref_frames[i]['s_array']
            ref_p_array = ref_frames[i]['p_array']

            del_i_array = frames['i_array'] - ref_i_array
            del_s_array = frames['s_array'] - ref_s_array
            del_p_array = frames['p_array'] - ref_p_array

            dd_s = del_s_array.mean(1)[0:nrow_i]-del_i_array.mean(1)
            dd_p = del_p_array.mean(0)[0:ncol_i]-del_i_array.mean(0)
            mask_s = np.fabs(dd_s) < 50.
            mask_p = np.fabs(dd_p) < 50.

            s_correl[i, ifile-1] = np.corrcoef(del_s_array.mean(1)[0:nrow_i][mask_s],
                                               dd_s[mask_s])[0, 1]
            p_correl[i, ifile-1] = np.corrcoef(del_p_array.mean(0)[0:ncol_i][mask_p],
                                               dd_p[mask_p])[0, 1]

    sys.stdout.write("!\n")
    sys.stdout.flush()

    for i in range(16):
        figs.get_obj('row', 'axs').flat[i].hist(s_correl[i], bins=100, range=(-1., 1.))
        figs.get_obj('col', 'axs').flat[i].hist(p_correl[i], bins=100, range=(-1., 1.))

    outbase = bias_plot_basename(outdir, raft, run_num, slot, plotname="bias_correl")
    makedir_safe(outbase)
    figs.save_all(outbase)


def plot_oscan_amp_stack_slot(butler, slot_data, **kwargs):
    """Stack the overscan region from all the amps on a sensor
    to look for coherent read noise

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files']
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()


    figs = FigureDict()
    region_keys = ['i', 's', 'p']
    region_labels = ['Imaging region', 'Serial overscan', 'Parallel overscan']

    for rkey, rlabel in zip(region_keys, region_labels):
        for dkey in ['row', 'col']:
            figs.setup_figure("mean_%s_%s" % (dkey, rkey), title="%s, profile by %s" % (rlabel, dkey),
                              xlabel=dkey, ylabel="Mean [ADU]")
            figs.setup_figure("std_%s_%s" % (dkey, rkey), title="%s, profile by %s" % (rlabel, dkey),
                              xlabel=dkey, ylabel="Std [ADU]")
            figs.setup_figure("signif_%s_%s" % (dkey, rkey), title="%s, profile by %s" % (rlabel, dkey),
                              xlabel=dkey, ylabel="Significance [sigma]")


    if superbias_type is None:
        superbias_frame = None
    else:
        superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
        superbias_frame = get_ccd_from_id(None, superbias_file, mask_files)

    nfiles = len(bias_files)

    stack_arrays = {}

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)

        if ifile == 0:
            dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)

            for key, val in dim_array_dict.items():
                stack_arrays[key] = np.zeros((nfiles, 16, len(val)))

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

            for key in ['i', 's', 'p']:
                row_stack = stack_arrays["row_%s" % key]
                col_stack = stack_arrays["col_%s" % key]
                struct = array_struct(frames['%s_array' % key])
                row_stack[ifile, i] = struct['rows']
                col_stack[ifile, i] = struct['cols']

    sys.stdout.write("!\n")
    sys.stdout.flush()

    amp_means = {}
    for key, val in stack_arrays.items():
        amp_means[key] = val.mean(0).mean(1)

    for i in range(nfiles):
        for key, xvals in dim_array_dict.items():
            stack = stack_arrays[key]
            amp_mean = amp_means[key]
            amp_stack = (stack[i].T - amp_mean).T
            mean_val = amp_stack.mean(0)
            std_val = amp_stack.std(0)
            signif_val = mean_val / std_val
            figs.plot_single("mean_%s" % key, xvals, mean_val)
            figs.plot_single("std_%s" % key, xvals, std_val)
            figs.plot_single("signif_%s" % key, xvals, signif_val)

    outbase = bias_plot_basename(outdir, raft, run_num, slot,
                                 plotname="bias", bias_type=bias_type, superbias_type=superbias_type)
    makedir_safe(outbase)
    figs.save_all(outbase)


def plot_oscan_correl_raft(butler, raft_data, **kwargs):
    """Plot the correlations between the serial overscan for each amp on a raft

    @param butler (Butler)   The data butler
    @param raft_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        covar (bool)         Plot covariance instead of correlation
        db (str)             Which database to use
        outdir (str)         Output directory
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']

    covar = kwargs.get('covar', False)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    figs = FigureDict()
    title = 'Raft {}, {}'.format(raft, run_num)

    slots = 'S00 S01 S02 S10 S11 S12 S20 S21 S22'.split()
    overscans = []
    boundry = 10

    for slot in slots:
        bias_files = raft_data[slot]['bias_files']
        ccd = get_ccd_from_id(butler, bias_files[0], [])

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(butler, ccd, amp)
            bbox = regions['serial_overscan']
            im = get_raw_image(butler, ccd, amp)
            bbox.grow(-boundry)
            oscan_data = im[bbox]
            print (slot, amp, oscan_data.getArray().shape)
            overscans.append(oscan_data.getArray())
    namps = len(overscans)
    if covar:
        data = np.array([np.cov(overscans[i[0]].ravel(),
                                overscans[i[1]].ravel())[0, 1]
                         for i in itertools.product(range(namps), range(namps))])
    else:
        data = np.array([np.corrcoef(overscans[i[0]].ravel(),
                                     overscans[i[1]].ravel())[0, 1]
                         for i in itertools.product(range(namps), range(namps))])
    data = data.reshape((namps, namps))
    figs.plot_raft_correl_matrix("correl", data, title=title, slots=slots)

    if covar:
        outfile = os.path.join(outdir, "plots", raft,
                               '{}_{}_overscan_covar.png'.format(raft, run_num))
    else:
        outfile = os.path.join(outdir, "plots", raft,
                               '{}_{}_overscan_correlations.png'.format(raft, run_num))

    makedir_safe(outfile)
    figs.savefig("correl", outfile)


def plot_superbias_fft_slot(butler, slot_data, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a superbias frame

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    std = kwargs.get('std', False)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    mask_files = slot_data['mask_files']

    if butler is not None:
        sys.stdout.write("Ignoring butler in plot_superbias_fft_slot")

    superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
    superbias = get_ccd_from_id(None, superbias_file, mask_files)

    freqs_dict = get_readout_frequencies_from_ccd(None, superbias)

    figs = FigureDict()
    region_keys = ['i', 's', 'p']
    region_labels = ['Imaging region', 'Serial overscan', 'Parallel overscan']

    for rkey, rlabel in zip(region_keys, region_labels):
        figs.setup_amp_plots_grid("%s_row" % rkey, title="FFT of superbias %s mean by row" % rlabel,
                                  xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")

    amps = get_amp_list(None, superbias)
    for i, amp in enumerate(amps):

        image = get_raw_image(None, superbias, amp)
        regions = get_geom_regions(None, superbias, amp)
        frames = get_image_frames_2d(image, regions)

        for key in ['i', 's', 'p']:
            frame = frames["%s_array" % key]
            freqs = freqs_dict["freqs_%s" % key]
            struct = array_struct(frame-frame.mean(), do_std=std)
            fftpow = np.abs(fftpack.fft(struct['rows']))
            fftpow /= len(fftpow)/2
            figs.plot_fft("%s_row" % key, i, freqs, np.sqrt(fftpow))


    outbase = superbias_plot_basename(outdir, raft, run_num, slot,
                                      plotname="superbias_fft", superbias_type=superbias_type)
    makedir_safe(outbase)
    if std:
        outbase += "_std"
    figs.save_all(outbase)


def plot_superbias_struct_slot(butler, slot_data, **kwargs):
    """Plot the row-wise and col-wise struture  in a superbias frame

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    std = kwargs.get('std', False)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    mask_files = slot_data['mask_files']

    if butler is not None:
        sys.stdout.write("Ignoring butler in plot_superbias_fft_slot")

    superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
    superbias = get_ccd_from_id(None, superbias_file, mask_files)

    dim_array_dict = get_dimension_arrays_from_ccd(None, superbias)

    figs = FigureDict()
    region_keys = ['i', 's', 'p']
    region_labels = ['Imaging region', 'Serial overscan', 'Parallel overscan']

    for rkey, rlabel in zip(region_keys, region_labels):
        for dkey in ['row', 'col']:
            figs.setup_amp_plots_grid('%s_%s' % (rkey, dkey), title="%s, profile by %s" % (rlabel, dkey),
                                      xlabel=dkey, ylabel="ADU")

    amps = get_amp_list(None, superbias)
    for i, amp in enumerate(amps):

        image = get_raw_image(None, superbias, amp)
        regions = get_geom_regions(None, superbias, amp)
        frames = get_image_frames_2d(image, regions)

        for key in ['i', 's', 'p']:
            xrow = dim_array_dict["row_%s" % key]
            xcol = dim_array_dict["col_%s" % key]
            struct = array_struct(frames['%s_array' % key], do_std=std)
            figs.plot("%s_row" % key, i, xrow, struct['rows'])
            figs.plot("%s_col" % key, i, xcol, struct['cols'])

    outbase = superbias_plot_basename(outdir, raft, run_num, slot,
                                      plotname="superbias", superbias_type=superbias_type)
    makedir_safe(outbase)
    figs.save_all(outbase)
