"""Functions to analyse bias and superbias frames"""

import os
import sys
import numpy as np

from .mpl_utils import init_matplotlib_backend
init_matplotlib_backend()

import matplotlib.pyplot as plt
from scipy import fftpack

import lsst.afw.math as afwMath
import lsst.afw.image as afwImage
from lsst.eotest.sensor import MaskedCCD, makeAmplifierGeometry
import lsst.eotest.image_utils as imutil

from .file_utils import get_bias_and_mask_files_run, get_hardware_type_and_id,\
    superbias_filename, superbias_stat_filename,\
    bias_plot_basename, superbias_plot_basename,\
    makedir_safe

from .config_utils import DEFAULT_DB, DEFAULT_OUTDIR,\
    DEFAULT_STAT_TYPE, DEFAULT_BITPIX

from .plot_utils import FigureDict

from .image_utils import get_image_frames_2d, array_struct, unbias

from .iter_utils import EO_AnalyzeSlotTask, EO_AnalyzeRaftTask,\
    AnalysisIterator,\
    iterate_over_slots, iterate_over_rafts

from correlated_noise import raft_level_oscan_correlations

DEFAULT_BIAS_TYPE = 'spline'
DEFAULT_SUPERBIAS_TYPE = None

T_SERIAL = 2e-06
T_PARALLEL = 40e-06

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
        data_files = get_bias_and_mask_files_run(run_num, **kwargs)
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, run_num, data_files, **kwargs)
        elif htype == "LCA-11021":
            iterate_over_slots(self.task, hid, run_num, data_files, **kwargs)
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
        data_files = get_bias_and_mask_files_run(run_num, **kwargs)
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, run_num, data_files, **kwargs)
        elif htype == "LCA-11021":
            self.task.run(hid, run_num, data_files, **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))



def make_superbias_slot(raft, run_num, slot, slot_data, **kwargs):
    """Make superbias frame for one slot

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        bias (str)           Method to use for unbiasing
        stat (str)           Statistic to use to stack data
        outdir (str)         Output directory
        bitpix (int)         Output data format BITPIX field
        skip (bool)          Flag to skip making superbias, only produce plots
        plot (bool)          Plot superbias images
        stats_hist (bool)    Plot superbias summary histograms
    """
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

    oscan = makeAmplifierGeometry(bias_files[0])

    if stat_type.upper() in afwMath.__dict__ and\
            isinstance(afwMath.__dict__[stat_type.upper()], int):
        statistic = afwMath.__dict__[stat_type.upper()]
    else:
        raise ValueError("Can not convert %s to a valid statistic to perform stacking" % stat_type)

    if statistic == afwMath.MEDIAN:
        output_file = superbias_filename(outdir, raft, run_num, slot, bias_type)
    else:
        output_file = superbias_stat_filename(outdir, raft, run_num, slot,
                                              stat_type.lower(), bias_type)

    makedir_safe(output_file)

    if not kwargs.get('skip', False):
        imutil.superbias_file(bias_files,
                              oscan.serial_overscan,
                              outfile=output_file,
                              bias_method=bias_type,
                              bitpix=kwargs.get('bitpix', DEFAULT_BITPIX),
                              statistic=kwargs.get('statistic', afwMath.MEDIAN))

    figs = FigureDict()

    if kwargs.get('plot', False):
        figs.plot_sensor("img", output_file, mask_files)

    if kwargs.get('stats_hist', False):
        figs.histogram_array("hist", output_file, mask_files,
                             title="Historam of RMS of bias-images, per pixel",
                             xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                             nbins=200, vmin=0., vmax=20.)

    figs.save_all(output_file.replace('.fits', ''))


def plot_bias_v_row_slot(raft, run_num, slot, slot_data, **kwargs):
    """Plot the bias as function of row

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        bias (str)           Method to use for unbiasing
        outdir (str)         Output directory
    """
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files'][0:5]
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files: \n" % (slot, len(bias_files)))
    oscan = makeAmplifierGeometry(bias_files[0])
    nrow_s = oscan.serial_overscan.getHeight()
    xrow_s = np.linspace(0, nrow_s-1, nrow_s)

    figs = FigureDict()

    figs.setup_amp_plots_grid("val",
                              title="Bias by row",
                              xlabel="row",
                              ylabel="Magnitude [ADU]")

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = MaskedCCD(bias_file, mask_files=mask_files)

        for i, amp in enumerate(ccd):
            im = afwImage.ImageF(bias_file, amp+1)
            bim = imutil.bias_image(im, oscan.serial_overscan, bias_method=bias_type)
            bim_row_mean = bim.Factory(bim, oscan.serial_overscan).getArray().mean(1)
            figs.plot("val", i, xrow_s[0:len(bim_row_mean)], bim_row_mean)

    sys.stdout.write("!\n")
    sys.stdout.flush()

    output_file = bias_plot_basename(outdir, raft, run_num, slot, 'biasval', bias_type)
    makedir_safe(output_file)

    figs.savefig("val", output_file)



def plot_bias_fft_slot(raft, run_num, slot, slot_data, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a series of bias frames

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files']
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    oscan = makeAmplifierGeometry(bias_files[0])

    n_col_full = oscan.naxis1
    t_row = n_col_full*T_SERIAL + T_PARALLEL
    f_s = 1./t_row

    nrow_i = oscan.imaging.getHeight()
    nrow_s = oscan.serial_overscan.getHeight()
    nrow_p = oscan.parallel_overscan.getHeight()

    freqs_i = fftpack.fftfreq(nrow_i)*f_s
    freqs_s = fftpack.fftfreq(nrow_s)*f_s
    freqs_p = fftpack.fftfreq(nrow_p)*f_s

    figs = FigureDict()

    figs.setup_amp_plots_grid("i_row", title="FFT of imaging region mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
    figs.setup_amp_plots_grid("s_row", title="FFT of serial overscan mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
    figs.setup_amp_plots_grid("p_row", title="FFT of parallel overscan mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")

    if superbias_type is None:
        superbias_file = None
        superbias_frame = None
    else:
        superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
        superbias_frame = MaskedCCD(superbias_file, mask_files=mask_files)

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = MaskedCCD(bias_file, mask_files=mask_files)

        for i, amp in enumerate(ccd):

            image = unbias(ccd, amp, oscan, bias_type=bias_type, superbias_frame=superbias_frame)
            frames = get_image_frames_2d(image, oscan)

            for key, freqs in zip(['i', 's', 'p'], [freqs_i, freqs_s, freqs_p]):
                struct = array_struct(frames['%s_array' % key], do_std=std)
                fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
                fftpow /= len(fftpow)/2
                figs.plot_fft('%s_row' % key, i, freqs, np.sqrt(fftpow))

    sys.stdout.write("!\n")
    sys.stdout.flush()

    outbase = bias_plot_basename(outdir, raft, run_num, slot, "bias",
                                 bias_type, superbias_type)
    makedir_safe(outbase)
    figs.save_all(outbase)


def plot_bias_struct_slot(raft, run_num, slot, slot_data, **kwargs):
    """Plot the row-wise and col-wise struture
    in a series of bias frames

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files'][0:5]
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    oscan = makeAmplifierGeometry(bias_files[0])

    nrow_i = oscan.imaging.getHeight()
    nrow_s = oscan.serial_overscan.getHeight()
    nrow_p = oscan.parallel_overscan.getHeight()
    ncol_i = oscan.imaging.getWidth()
    ncol_s = oscan.serial_overscan.getWidth()
    ncol_p = oscan.parallel_overscan.getWidth()

    xrow_i = np.linspace(0, nrow_i-1, nrow_i)
    xrow_s = np.linspace(0, nrow_s-1, nrow_s)
    xrow_p = np.linspace(0, nrow_p-1, nrow_p)
    xcol_i = np.linspace(0, ncol_i-1, ncol_i)
    xcol_s = np.linspace(0, ncol_s-1, ncol_s)
    xcol_p = np.linspace(0, ncol_p-1, ncol_p)

    figs = FigureDict()
    figs.setup_amp_plots_grid('i_row', title="Imaging region, profile by row",
                              xlabel="row", ylabel="ADU")
    figs.setup_amp_plots_grid('i_col', title="Imaging region, profile by col",
                              xlabel="col", ylabel="ADU")
    figs.setup_amp_plots_grid('s_row', title="Serial overscan, profile by row",
                              xlabel="row", ylabel="ADU")
    figs.setup_amp_plots_grid('s_col', title="Serial overscan, profile by row",
                              xlabel="col", ylabel="ADU")
    figs.setup_amp_plots_grid('p_row', title="Parallel overscan, profile by row",
                              xlabel="row", ylabel="ADU")
    figs.setup_amp_plots_grid('p_col', title="Parallel overscan, profile by row",
                              xlabel="col", ylabel="ADU")

    if superbias_type is None:
        superbias_file = None
        superbias_frame = None
    else:
        superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
        superbias_frame = MaskedCCD(superbias_file, mask_files=mask_files)

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = MaskedCCD(bias_file, mask_files=mask_files)

        for i, amp in enumerate(ccd):

            image = unbias(ccd, amp, oscan, bias_type=bias_type, superbias_frame=superbias_frame)
            frames = get_image_frames_2d(image, oscan)

            for key, xrow, xcol in zip(['i', 's', 'p'],
                                       [xrow_i, xrow_s, xrow_p],
                                       [xcol_i, xcol_s, xcol_p]):

                struct = array_struct(frames['%s_array' % key], do_std=std)
                figs.plot("%i_row" % key, i, xrow, struct['rows'])
                figs.plot("%i_col" % key, i, xcol, struct['cols'])

    sys.stdout.write("!\n")
    sys.stdout.flush()
    outbase = bias_plot_basename(outdir, raft, run_num, slot, "bias", bias_type, superbias_type)
    makedir_safe(outbase)

    if std:
        outbase += "_std"

    figs.save_all(outbase)


def plot_correl_wrt_oscan_scan(raft, run_num, slot, slot_data, **kwargs):
    """Plot the correlations between the imaging section
    and the overscan regions in a series of bias frames

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        outdir (str)         Output directory
    """
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files']
    #mask_files = slot_data['mask_files']

    nfiles = len(bias_files)

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    oscan = makeAmplifierGeometry(bias_files[0])

    nrow_i = oscan.imaging.getHeight()
    ncol_i = oscan.imaging.getWidth()


    figs = FigureDict()

    figs.setup_amp_plots_grid("row", title="Correlation: imaging region and serial overscan",
                              xlabel="Correlation",
                              ylabel="Number of frames")
    figs.setup_amp_plots_grid("col", title="Correlation: imaging region and paralell overscan",
                              xlabel="Correlation",
                              ylabel="Number of frames")

    ref_images = {}

    s_correl = np.ndarray((16, nfiles-1))
    p_correl = np.ndarray((16, nfiles-1))

    for ifile, f in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = MaskedCCD(f)

        for i, amp in enumerate(ccd):
            img = ccd[amp]
            images = get_image_frames_2d(img, ccd.amp_geom)
            if ifile == 0:
                ref_images[i] = images
                continue

            ref_i_array = ref_images[i]['i_array']
            ref_s_array = ref_images[i]['s_array']
            ref_p_array = ref_images[i]['p_array']

            del_i_array = images['i_array'] - ref_i_array
            del_s_array = images['s_array'] - ref_s_array
            del_p_array = images['p_array'] - ref_p_array

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

    outbase = bias_plot_basename(outdir, raft, run_num, slot, "bias_correl")
    makedir_safe(outbase)
    figs.save_all(outbase)


def plot_oscan_amp_stack_slot(raft, run_num, slot, slot_data, **kwargs):
    """Stack the overscan region from all the amps on a sensor
    to look for coherent read noise

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
    """
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    bias_files = slot_data['bias_files']
    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    oscan = makeAmplifierGeometry(bias_files[0])

    nrow_i = oscan.imaging.getHeight()
    nrow_s = oscan.serial_overscan.getHeight()
    nrow_p = oscan.parallel_overscan.getHeight()
    ncol_i = oscan.imaging.getWidth()
    ncol_s = oscan.serial_overscan.getWidth()
    ncol_p = oscan.parallel_overscan.getWidth()

    xrow_i = np.linspace(0, nrow_i-1, nrow_i)
    xrow_s = np.linspace(0, nrow_s-1, nrow_s)
    xrow_p = np.linspace(0, nrow_p-1, nrow_p)
    xcol_i = np.linspace(0, ncol_i-1, ncol_i)
    xcol_s = np.linspace(0, ncol_s-1, ncol_s)
    xcol_p = np.linspace(0, ncol_p-1, ncol_p)

    figs = FigureDict()

    figs.setup_figure("mean_i_row", title="Imaging region, profile by row",
                      xlabel="row", ylabel="Mean [ADU]")
    figs.setup_figure("mean_i_col", title="Imaging region, profile by col",
                      xlabel="col", ylabel="Mean [ADU]")
    figs.setup_figure("mean_s_row", title="Serial overscan, profile by row",
                      xlabel="row", ylabel="Mean [ADU]")
    figs.setup_figure("mean_s_col", title="Serial overscan, profile by col",
                      xlabel="col", ylabel="Mean [ADU]")
    figs.setup_figure("mean_p_row", title="Parallel overscan, profile by row",
                      xlabel="row", ylabel="Mean [ADU]")
    figs.setup_figure("mean_p_col", title="Parallel overscan, profile by col",
                      xlabel="col", ylabel="Mean [ADU]")

    figs.setup_figure("std_i_row", title="Imaging region, profile by row",
                      xlabel="row", ylabel="Std [ADU]")
    figs.setup_figure("std_i_col", title="Imaging region, profile by col",
                      xlabel="col", ylabel="Std [ADU]")
    figs.setup_figure("std_s_row", title="Serial overscan, profile by row",
                      xlabel="row", ylabel="Std [ADU]")
    figs.setup_figure("std_s_col", title="Serial overscan, profile by col",
                      xlabel="col", ylabel="Std [ADU]")
    figs.setup_figure("std_p_row", title="Parallel overscan, profile by row",
                      xlabel="row", ylabel="Std [ADU]")
    figs.setup_figure("std_p_col", title="Parallel overscan, profile by col",
                      xlabel="col", ylabel="Std [ADU]")

    figs.setup_figure("signif_i_row", title="Imaging region, profile by row",
                      xlabel="row",
                      ylabel="Significance [sigma]")
    figs.setup_figure("signif_i_col", title="Imaging region, profile by col",
                      xlabel="col",
                      ylabel="Significance [sigma]")
    figs.setup_figure("signif_s_row", title="Serial overscan, profile by row",
                      xlabel="row",
                      ylabel="Significance [sigma]")
    figs.setup_figure("signif_s_col", title="Serial overscan, profile by row",
                      xlabel="col",
                      ylabel="Significance [sigma]")
    figs.setup_figure("signif_p_row", title="Parallel overscan, profile by row",
                      xlabel="row",
                      ylabel="Significance [sigma]")
    figs.setup_figure("signif_p_col", title="Parallel overscan, profile by row",
                      xlabel="col",
                      ylabel="Significance [sigma]")

    if superbias_type is None:
        superbias_file = None
        superbias_frame = None
    else:
        superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
        superbias_frame = MaskedCCD(superbias_file, mask_files=mask_files)

    nfiles = len(bias_files)

    i_row_stack = np.zeros((nfiles, 16, nrow_i))
    i_col_stack = np.zeros((nfiles, 16, ncol_i))
    s_row_stack = np.zeros((nfiles, 16, nrow_s))
    s_col_stack = np.zeros((nfiles, 16, ncol_s))
    p_row_stack = np.zeros((nfiles, 16, nrow_p))
    p_col_stack = np.zeros((nfiles, 16, ncol_p))

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = MaskedCCD(bias_file, mask_files=mask_files)

        for i, amp in enumerate(ccd):

            image = unbias(ccd, amp, oscan, bias_type=bias_type, superbias_frame=superbias_frame)
            frames = get_image_frames_2d(image, oscan)

            for key, row_stack, col_stack in zip(['i', 's', 'p'],
                                                 [i_row_stack, s_row_stack, p_row_stack],
                                                 [i_col_stack, s_col_stack, p_col_stack]):

                struct = array_struct(frames['%s_array' % key])
                row_stack[ifile, i] = struct['rows']
                col_stack[ifile, i] = struct['cols']


    sys.stdout.write("!\n")
    sys.stdout.flush()

    amp_mean_i_row = i_row_stack.mean(0).mean(1)
    amp_mean_i_col = i_col_stack.mean(0).mean(1)
    amp_mean_s_row = s_row_stack.mean(0).mean(1)
    amp_mean_s_col = s_col_stack.mean(0).mean(1)
    amp_mean_p_row = p_row_stack.mean(0).mean(1)
    amp_mean_p_col = p_col_stack.mean(0).mean(1)

    for i in range(nfiles):

        for key, stack, xvals, amp_mean in zip(["i_row", "i_col", "s_row", "s_col", "p_row", "p_col"],
                                               [i_row_stack, i_col_stack, s_row_stack,
                                                s_col_stack, p_row_stack, p_col_stack],
                                               [xrow_i, xcol_i, xrow_s, xcol_s, xrow_p, xcol_p],
                                               [amp_mean_i_row, amp_mean_i_col, amp_mean_s_row,
                                                amp_mean_s_col, amp_mean_p_row, amp_mean_p_col]):
            amp_stack = (stack[i].T - amp_mean).T
            mean_val = amp_stack.mean(0)
            std_val = amp_stack.std(0)
            signif_val = mean_val / std_val
            figs.plot_single("mean_%s" % key, xvals, mean_val)
            figs.plot_single("std_%s" % key, xvals, std_val)
            figs.plot_single("signif_%s" % key, xvals, signif_val)

    outbase = bias_plot_basename(outdir, raft, run_num, slot, "bias", bias_type, superbias_type)
    makedir_safe(outbase)
    figs.save_all(outbase)


def plot_oscan_correl_raft(raft, run_num, raft_data, **kwargs):
    """Plot the correlations between the serial overscan for each amp on a raft

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_data:   dict
       Dictionary pointing to the bias  files

    Keyword arguments
    -----------------
    covar:       bool
    db:          str
    outdir:       str
    """

    covar = kwargs.get('covar', False)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    #all_bias_files = get_bias_files_run(run_num, acq_types=ACQ_TYPES_DEFAULT[0:1], db=db)
    #bias_files = {key : val[0] for key, val in all_bias_files.items()}
    bias_files = raft_data['bias_files']

    title = 'Raft {}, {}'.format(raft, run_num)
    fig = raft_level_oscan_correlations(bias_files, title=title, covar=covar)
    if covar:
        outfile = os.path.join(outdir, "plots", raft,
                               '{}_{}_overscan_covar.png'.format(raft, run_num))
    else:
        outfile = os.path.join(outdir, "plots", raft,
                               '{}_{}_overscan_correlations.png'.format(raft, run_num))

    makedir_safe(outfile)
    fig[0].savefig(outfile)
    plt.close(fig[0])



def plot_superbias_fft_slot(raft, run_num, slot, slot_data, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a superbias frame

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    std = kwargs.get('std', False)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s.\n")
    sys.stdout.flush()

    superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
    superbias = MaskedCCD(superbias_file, mask_files=mask_files)
    oscan = superbias.amp_geom

    n_col_full = oscan.naxis1
    t_row = n_col_full*T_SERIAL + T_PARALLEL
    f_s = 1./t_row

    nrow_i = oscan.imaging.getHeight()
    nrow_s = oscan.serial_overscan.getHeight()
    nrow_p = oscan.parallel_overscan.getHeight()

    freqs_i = fftpack.fftfreq(nrow_i)*f_s
    freqs_s = fftpack.fftfreq(nrow_s)*f_s
    freqs_p = fftpack.fftfreq(nrow_p)*f_s

    figs = FigureDict()
    figs.setup_amp_plots_grid("i_row", title="FFT of superbias imaging region mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
    figs.setup_amp_plots_grid("s_row", title="FFT of superbias serial overscan mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
    figs.setup_amp_plots_grid("p_row", title="FFT of superbias parallel overscan mean by row",
                              xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")

    for i, amp in enumerate(superbias):

        image = superbias[amp]
        frames = get_image_frames_2d(image, oscan)

        for key, freqs in zip(['i', 's', 'p'],
                              [freqs_i, freqs_s, freqs_p]):
            frame = frames['%s_array' % key]
            struct = array_struct(frame-frame.mean(), do_std=std)

            fftpow = np.abs(fftpack.fft(struct['rows']))
            fftpow /= len(fftpow)/2

            figs.plot_fft("%i_row" % key, i, freqs, np.sqrt(fftpow))

    outbase = superbias_plot_basename(outdir, raft, run_num, slot, "superbias", superbias_type)
    makedir_safe(outbase)
    if std:
        outbase += "_std"
    figs.save_all(outbase)


def plot_superbias_struct_slot(raft, run_num, slot, slot_data, **kwargs):
    """Plot the row-wise and col-wise struture  in a superbias frame

    @param raft (str)        Raft name, i.e., 'RTM-004-Dev'
    @param run_num (str)     Run number, i.e,. '6106D'
    @param slot (str)        Slot in question
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    std = kwargs.get('std', False)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)

    mask_files = slot_data['mask_files']

    sys.stdout.write("Working on %s.\n")
    sys.stdout.flush()

    superbias_file = superbias_filename(outdir, raft, run_num, slot, superbias_type)
    superbias = MaskedCCD(superbias_file, mask_files=mask_files)
    oscan = superbias.amp_geom

    nrow_i = oscan.imaging.getHeight()
    nrow_s = oscan.serial_overscan.getHeight()
    nrow_p = oscan.parallel_overscan.getHeight()
    ncol_i = oscan.imaging.getWidth()
    ncol_s = oscan.serial_overscan.getWidth()
    ncol_p = oscan.parallel_overscan.getWidth()

    xrow_i = np.linspace(0, nrow_i-1, nrow_i)
    xrow_s = np.linspace(0, nrow_s-1, nrow_s)
    xrow_p = np.linspace(0, nrow_p-1, nrow_p)
    xcol_i = np.linspace(0, ncol_i-1, ncol_i)
    xcol_s = np.linspace(0, ncol_s-1, ncol_s)
    xcol_p = np.linspace(0, ncol_p-1, ncol_p)

    figs = FigureDict()

    figs.setup_amp_plots_grid("i_row", title="Imaging region, profile by row",
                              xlabel="row", ylabel="ADU")
    figs.setup_amp_plots_grid("i_col", title="Imaging region, profile by col",
                              xlabel="col", ylabel="ADU")
    figs.setup_amp_plots_grid("s_row", title="Serial overscan, profile by row",
                              xlabel="row", ylabel="ADU")
    figs.setup_amp_plots_grid("s_col", title="Serial overscan, profile by row",
                              xlabel="col", ylabel="ADU")
    figs.setup_amp_plots_grid("p_row", title="Parallel overscan, profile by row",
                              xlabel="row", ylabel="ADU")
    figs.setup_amp_plots_grid("p_col", title="Parallel overscan, profile by row",
                              xlabel="col", ylabel="ADU")

    for i, amp in enumerate(superbias):

        image = superbias[amp]
        frames = get_image_frames_2d(image, oscan)

        for key, xrow, xcol in zip(['i', 's', 'p'],
                                   [xrow_i, xrow_s, xrow_p],
                                   [xcol_i, xcol_s, xcol_p]):
            struct = array_struct(frames['%s_array' % key], do_std=std)
            figs.plot("%s_row" % key, i, xrow, struct['rows'])
            figs.plot("%s_col" % key, i, xcol, struct['cols'])

    outbase = superbias_plot_basename(outdir, raft, run_num, slot, "superbias", superbias_type)
    makedir_safe(outbase)
    figs.save_all(outbase)
