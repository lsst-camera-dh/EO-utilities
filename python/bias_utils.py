"""Functions to analyse bias and superbias frames"""

import os
import sys
import numpy as np

from mpl_utils import init_matplotlib_backend
init_matplotlib_backend()

import matplotlib.pyplot as plt
from scipy import fftpack

import lsst.afw.math as afwMath
from lsst.eotest.sensor import MaskedCCD, makeAmplifierGeometry
import lsst.eotest.image_utils as imutil

from correlated_noise import raft_level_oscan_correlations

from file_utils import get_bias_files_slot, get_mask_files_slot,\
    get_bias_files_raft, get_bias_files_RandD,\
    ACQ_TYPES_DEFAULT, MASK_TYPES_DEFAULT, RAFT_ROOT_FOLDER
from plot_utils import setup_figure, setup_amp_plots_grid,\
    plot_fft, plot_sensor, historgram_array
from image_utils import get_image_frames_2d, array_struct

DEFAULT_BIAS_TYPE = 'spline'
DEFAULT_STAT_TYPE = 'median'
DEFAULT_SUPERBIAS_TYPE = None

BITPIX = -32
T_SERIAL = 2e-06
T_PARALLEL = 40e-06
ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']


def run_make_superbias(raft, run_num, slot_list, **kwargs):
    """Make superbias frames

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_list:   list
       List of slots

    Keyword arguments
    -----------------
    acq_types:    list
    mask_types:   list
    root_dir:     string
    mask:         bool
    skip:         bool
    bias:         str
    stat_type     str
    plot          bool
    stats_hist    bool
    """
    acq_types = kwargs.get('acq_types', ACQ_TYPES_DEFAULT)
    mask_types = kwargs.get('mask_types', MASK_TYPES_DEFAULT)
    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)
    mask = kwargs.get('mask', False)
    skip = kwargs.get('skip', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    stat_type = kwargs.get('stat', DEFAULT_STAT_TYPE)
    plot = kwargs.get('plot', False)
    stats_hist = kwargs.get('stats_hist', False)

    if stat_type.upper() in afwMath.__dict__ and\
            isinstance(afwMath.__dict__[stat_type.upper()], int):
        statistic = afwMath.__dict__[stat_type.upper()]
    else:
        raise ValueError("Can not convert %s to a valid statistic to perform stacking" % stat_type)

    # If we are doing more that one slot, don't show the plots
    if len(slot_list) > 1:
        plt.ioff()
    else:
        plt.ion()

    for slot in slot_list:

        sys.stdout.write("Working on %s\n" % slot)

        bias_files = get_bias_files_slot(raft, run_num, slot, acq_types, root_dir)
        if mask:
            sensor_id = (os.path.splitext(os.path.split(bias_files[0])[-1])[0]).split('_')[0]
            mask_files = get_mask_files_slot(raft, run_num, sensor_id, mask_types, root_dir)
        else:
            mask_files = []

        oscan = makeAmplifierGeometry(bias_files[0])

        if statistic == afwMath.MEDIAN:
            output_file = os.path.join('superbias',
                                       '%s-%s-%s_superbias_b-%s.fits' %\
                                           (raft, run_num, slot, bias_type))
        else:
            output_file = os.path.join('superbias',
                                       '%s-%s-%s_%s_b-%s.fits' %\
                                           (raft, run_num, slot, stat_type.lower(), bias_type))

        if not skip:
            imutil.superbias_file(bias_files[::2],
                                  oscan.serial_overscan,
                                  outfile=output_file,
                                  bias_method=bias_type,
                                  bitpix=BITPIX,
                                  statistic=statistic)

        if plot:
            fig_sensor = plot_sensor(output_file, mask_files)
            fig_sensor[0].savefig(output_file.replace('.fits', '.png'))

        if stats_hist:
            fig_hist = historgram_array(output_file, mask_files,
                                        "RMS [counts]", "Pixels / 0.1 counts",
                                        nbins=200, vmin=0., vmax=20.)
            fig_hist[0].savefig(output_file.replace('.fits', '_hist.png'))



def run_plot_bias_fft(raft, run_num, slot_list, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a series of bias frames

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_list:   list
       List of slots

    Keyword arguments
    -----------------
    acq_types:      list
    mask_types:     list
    root_dir:       string
    mask:           bool
    std:            bool
    bias:           str
    superbias:      str
    """
    acq_types = kwargs.get('acq_types', ACQ_TYPES_DEFAULT)
    mask_types = kwargs.get('mask_types', MASK_TYPES_DEFAULT)
    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)
    mask = kwargs.get('mask', False)
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)

    # If we are doing more that one slot, don't show the plots
    if len(slot_list) > 1:
        plt.ioff()
    else:
        plt.ion()

    for slot in slot_list:

        bias_files = get_bias_files_slot(raft, run_num, slot, acq_types, root_dir)
        if mask:
            sensor_id = (os.path.splitext(os.path.split(bias_files[0])[-1])[0]).split('_')[0]
            mask_files = get_mask_files_slot(raft, run_num, sensor_id, mask_types, root_dir)
        else:
            mask_files = []

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

        fig_raw_i_row, axs_raw_i_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_s_row, axs_raw_s_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_p_row, axs_raw_p_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))

        if superbias_type is None:
            superbias_file = None
            superbias_frame = None
        else:
            superbias_file = os.path.join('superbias',
                                          '%s-%s-%s_superbias_b-%s.fits' %\
                                              (raft, run_num, slot, superbias_type))
            superbias_frame = MaskedCCD(superbias_file, mask_files=mask_files)

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = MaskedCCD(bias_file, mask_files=mask_files)

            for i, amp in enumerate(ccd):

                if bias_type is not None:
                    image = imutil.unbias_and_trim(ccd[amp], oscan.serial_overscan,
                                                   bias_method=bias_type)
                else:
                    image = ccd[amp]

                if superbias_frame is not None:
                    image -= superbias_frame[amp]

                frames = get_image_frames_2d(image, oscan)

                i_struct = array_struct(frames['i_array'], do_std=std)
                s_struct = array_struct(frames['s_array'], do_std=std)
                p_struct = array_struct(frames['p_array'], do_std=std)

                fftpow_i = np.abs(fftpack.fft(i_struct['rows']-i_struct['rows'].mean()))
                fftpow_s = np.abs(fftpack.fft(s_struct['rows']-s_struct['rows'].mean()))
                fftpow_p = np.abs(fftpack.fft(p_struct['rows']-p_struct['rows'].mean()))

                fftpow_i /= len(fftpow_i)/2
                fftpow_s /= len(fftpow_s)/2
                fftpow_p /= len(fftpow_p)/2

                plot_fft(axs_raw_i_row.flat[i], freqs_i, fftpow_i)
                plot_fft(axs_raw_s_row.flat[i], freqs_s, fftpow_s)
                plot_fft(axs_raw_p_row.flat[i], freqs_p, fftpow_p)


        sys.stdout.write("!\n")
        outbase = os.path.join("superbias", "plots", "%s_%s_%s" % (raft, run_num, slot))

        if bias_type is None:
            outbase += "_b-none"
        else:
            outbase += "_b-%s" % bias_type

        if superbias_type is None:
            outbase += "_s-none"
        else:
            outbase += "_s-%s" % superbias_type

        if std:
            outbase += "_std"

        fig_raw_i_row.savefig("%s_fft_i_row.png" % outbase)
        fig_raw_s_row.savefig("%s_fft_s_row.png" % outbase)
        fig_raw_p_row.savefig("%s_fft_p_row.png" % outbase)


def run_plot_bias_struct(raft, run_num, slot_list, **kwargs):
    """Plot the row-wise and col-wise struture
    in a series of bias frames

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_list:   list
       List of slots

    Keyword arguments
    -----------------
    acq_types:      list
    mask_types:     list
    root_dir:       string
    mask:           bool
    std:            bool
    bias:           str
    superbias:      str
    """
    acq_types = kwargs.get('acq_types', ACQ_TYPES_DEFAULT)
    mask_types = kwargs.get('mask_types', MASK_TYPES_DEFAULT)
    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)
    mask = kwargs.get('mask', False)
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
 
   # If we are doing more that one slot, don't show the plots
    if len(slot_list) > 1:
        plt.ioff()
    else:
        plt.ion()

    for slot in slot_list:

        bias_files = get_bias_files_slot(raft, run_num, slot, acq_types, root_dir)
        if mask:
            sensor_id = (os.path.splitext(os.path.split(bias_files[0])[-1])[0]).split('_')[0]
            mask_files = get_mask_files_slot(raft, run_num, sensor_id, mask_types, root_dir)
        else:
            mask_files = []

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

        fig_raw_i_row, axs_raw_i_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_i_col, axs_raw_i_col = setup_amp_plots_grid("col", "counts", figsize=(15, 10))
        fig_raw_s_row, axs_raw_s_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_s_col, axs_raw_s_col = setup_amp_plots_grid("col", "counts", figsize=(15, 10))
        fig_raw_p_row, axs_raw_p_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_p_col, axs_raw_p_col = setup_amp_plots_grid("col", "counts", figsize=(15, 10))

        if superbias_type is None:
            superbias_file = None
            superbias_frame = None
        else:
            superbias_file = os.path.join('superbias',
                                          '%s-%s-%s_superbias_b-%s.fits' %\
                                              (raft, run_num, slot, superbias_type))
            superbias_frame = MaskedCCD(superbias_file, mask_files=mask_files)

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = MaskedCCD(bias_file, mask_files=mask_files)

            for i, amp in enumerate(ccd):

                if bias_type is not None:
                    image = imutil.unbias_and_trim(ccd[amp], oscan.serial_overscan,
                                                   bias_method=bias_type)
                else:
                    image = ccd[amp]

                if superbias_frame is not None:
                    image -= superbias_frame[amp]

                frames = get_image_frames_2d(image, oscan)

                i_struct = array_struct(frames['i_array'], do_std=std)
                s_struct = array_struct(frames['s_array'], do_std=std)
                p_struct = array_struct(frames['p_array'], do_std=std)

                ax_raw_i_row = axs_raw_i_row.flat[i]
                ax_raw_i_col = axs_raw_i_col.flat[i]
                ax_raw_s_row = axs_raw_s_row.flat[i]
                ax_raw_s_col = axs_raw_s_col.flat[i]
                ax_raw_p_row = axs_raw_p_row.flat[i]
                ax_raw_p_col = axs_raw_p_col.flat[i]

                ax_raw_i_row.plot(xrow_i, i_struct['rows'])
                ax_raw_i_col.plot(xcol_i, i_struct['cols'])
                ax_raw_s_row.plot(xrow_s, s_struct['rows'])
                ax_raw_s_col.plot(xcol_s, s_struct['cols'])
                ax_raw_p_row.plot(xrow_p, p_struct['rows'])
                ax_raw_p_col.plot(xcol_p, p_struct['cols'])


        sys.stdout.write("!\n")
        outbase = os.path.join("superbias", "plots", "%s_%s_%s" % (raft, run_num, slot))

        if bias_type is None:
            outbase += "_b-none"
        else:
            outbase += "_b-%s" % bias_type

        if superbias_type is None:
            outbase += "_s-none"
        else:
            outbase += "_s-%s" % superbias_type

        if std:
            outbase += "_std"

        fig_raw_i_row.savefig("%s_i_row.png" % outbase)
        fig_raw_i_col.savefig("%s_i_col.png" % outbase)
        fig_raw_s_row.savefig("%s_s_row.png" % outbase)
        fig_raw_s_col.savefig("%s_s_col.png" % outbase)
        fig_raw_p_row.savefig("%s_p_row.png" % outbase)
        fig_raw_p_col.savefig("%s_p_col.png" % outbase)




def run_plot_correl_wrt_oscan(raft, run_num, slot_list, **kwargs):
    """Plot the correlations between the imaging section
    and the overscan regions in a series of bias frames

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_list:   list
       List of slots

    Keyword arguments
    -----------------
    acq_types:      list
    root_dir:       string
    """

    acq_types = kwargs.get('acq_types', ACQ_TYPES_DEFAULT)
    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)

    for slot in slot_list:

        bias_files = get_bias_files_slot(raft, run_num, slot, acq_types, root_dir)
        nfiles = len(bias_files)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        oscan = makeAmplifierGeometry(bias_files[0])

        nrow_i = oscan.imaging.getHeight()
        ncol_i = oscan.imaging.getWidth()

        fig_correl_row, axs_correl_row = setup_amp_plots_grid("Serial OS [counts]",
                                                              "Delta [counts]", figsize=(15, 10))
        fig_correl_col, axs_correl_col = setup_amp_plots_grid("Parallel OS [counts]",
                                                              "Delta [counts]", figsize=(15, 10))

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


        for i in range(16):
            ax_correl_row = axs_correl_row.flat[i]
            ax_correl_col = axs_correl_col.flat[i]
            ax_correl_row.hist(s_correl[i], bins=100, range=(-1., 1.))
            ax_correl_col.hist(p_correl[i], bins=100, range=(-1., 1.))

        outbase = os.path.join("bias_results", "plots", "%s_%s_%s" % (raft, run_num, slot))
        fig_correl_row.savefig("%s_correl_row.png" % outbase)
        fig_correl_col.savefig("%s_correl_col.png" % outbase)



def run_plot_oscan_amp_stack(raft, run_num, slot_list, **kwargs):
    """Stack the overscan region from all the amps on a sensor
    to look for coherent read noise

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_list:   list
       List of slots

    Keyword arguments
    -----------------
    acq_types:      list
    mask_types:     list
    root_dir:       string
    mask:           bool
    bias_type:      str
    superbias_type: str
    """

    acq_types = kwargs.get('acq_types', ACQ_TYPES_DEFAULT)
    mask_types = kwargs.get('mask_types', MASK_TYPES_DEFAULT)
    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)
    mask = kwargs.get('mask', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)

    # If we are doing more that one slot, don't show the plots
    if len(slot_list) > 1:
        plt.ioff()
    else:
        plt.ion()
        
    for slot in slot_list:

        bias_files = get_bias_files_slot(raft, run_num, slot, acq_types, root_dir)
        if mask:
            sensor_id = (os.path.splitext(os.path.split(bias_files[0])[-1])[0]).split('_')[0]
            mask_files = get_mask_files_slot(raft, run_num, sensor_id, mask_types, root_dir)
        else:
            mask_files = []

        bias_files = bias_files[0:5]

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

        fig_mean_i_row, ax_mean_i_row = setup_figure("row", "Mean [counts]",
                                                     figsize=(15, 10))
        fig_mean_i_col, ax_mean_i_col = setup_figure("col", "Mean [counts]",
                                                     figsize=(15, 10))
        fig_mean_s_row, ax_mean_s_row = setup_figure("row", "Mean [counts]",
                                                     figsize=(15, 10))
        fig_mean_s_col, ax_mean_s_col = setup_figure("col", "Mean [counts]",
                                                     figsize=(15, 10))
        fig_mean_p_row, ax_mean_p_row = setup_figure("row", "Mean [counts]",
                                                     figsize=(15, 10))
        fig_mean_p_col, ax_mean_p_col = setup_figure("col", "Mean [counts]",
                                                     figsize=(15, 10))

        fig_std_i_row, ax_std_i_row = setup_figure("row", "Std [counts]", figsize=(15, 10))
        fig_std_i_col, ax_std_i_col = setup_figure("col", "Std [counts]", figsize=(15, 10))
        fig_std_s_row, ax_std_s_row = setup_figure("row", "Std [counts]", figsize=(15, 10))
        fig_std_s_col, ax_std_s_col = setup_figure("col", "Std [counts]", figsize=(15, 10))
        fig_std_p_row, ax_std_p_row = setup_figure("row", "Std [counts]", figsize=(15, 10))
        fig_std_p_col, ax_std_p_col = setup_figure("col", "Std [counts]", figsize=(15, 10))

        fig_signif_i_row, ax_signif_i_row = setup_figure("row", "Significance [sigma]",
                                                         figsize=(15, 10))
        fig_signif_i_col, ax_signif_i_col = setup_figure("col", "Significance [sigma]",
                                                         figsize=(15, 10))
        fig_signif_s_row, ax_signif_s_row = setup_figure("row", "Significance [sigma]",
                                                         figsize=(15, 10))
        fig_signif_s_col, ax_signif_s_col = setup_figure("col", "Significance [sigma]",
                                                         figsize=(15, 10))
        fig_signif_p_row, ax_signif_p_row = setup_figure("row", "Significance [sigma]",
                                                         figsize=(15, 10))
        fig_signif_p_col, ax_signif_p_col = setup_figure("col", "Significance [sigma]",
                                                         figsize=(15, 10))

        if superbias_type is None:
            superbias_file = None
            superbias_frame = None
        else:
            superbias_file = os.path.join('superbias',
                                          '%s-%s-%s_superbias_b-%s.fits' %\
                                              (raft, run_num, slot, superbias_type))
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
                if bias_type is not None:
                    image = imutil.unbias_and_trim(ccd[amp], oscan.serial_overscan,
                                                   bias_method=bias_type)
                else:
                    image = ccd[amp]

                if superbias_frame is not None:
                    image -= superbias_frame[amp]

                frames = get_image_frames_2d(image, oscan)

                i_struct = array_struct(frames['i_array'])
                s_struct = array_struct(frames['s_array'])
                p_struct = array_struct(frames['p_array'])

                i_row_stack[ifile, i] = i_struct['rows']
                i_col_stack[ifile, i] = i_struct['cols']

                s_row_stack[ifile, i] = s_struct['rows']
                s_col_stack[ifile, i] = s_struct['cols']

                p_row_stack[ifile, i] = p_struct['rows']
                p_col_stack[ifile, i] = p_struct['cols']


        amp_mean_i_row = i_row_stack.mean(0).mean(1)
        amp_mean_i_col = i_col_stack.mean(0).mean(1)
        amp_mean_s_row = s_row_stack.mean(0).mean(1)
        amp_mean_s_col = s_col_stack.mean(0).mean(1)
        amp_mean_p_row = p_row_stack.mean(0).mean(1)
        amp_mean_p_col = p_col_stack.mean(0).mean(1)

        for i in range(nfiles):
            amp_stack_i_row = (i_row_stack[i].T - amp_mean_i_row).T
            amp_stack_i_col = (i_col_stack[i].T - amp_mean_i_col).T
            amp_stack_s_row = (s_row_stack[i].T - amp_mean_s_row).T
            amp_stack_s_col = (s_col_stack[i].T - amp_mean_s_col).T
            amp_stack_p_row = (p_row_stack[i].T - amp_mean_p_row).T
            amp_stack_p_col = (p_col_stack[i].T - amp_mean_p_col).T

            mean_i_row = amp_stack_i_row.mean(0)
            mean_i_col = amp_stack_i_col.mean(0)
            mean_s_row = amp_stack_s_row.mean(0)
            mean_s_col = amp_stack_s_col.mean(0)
            mean_p_row = amp_stack_p_row.mean(0)
            mean_p_col = amp_stack_p_col.mean(0)

            std_i_row = amp_stack_i_row.std(0)
            std_i_col = amp_stack_i_col.std(0)
            std_s_row = amp_stack_s_row.std(0)
            std_s_col = amp_stack_s_col.std(0)
            std_p_row = amp_stack_p_row.std(0)
            std_p_col = amp_stack_p_col.std(0)

            signif_i_row = mean_i_row / std_i_row
            signif_i_col = mean_i_col / std_i_col
            signif_s_row = mean_s_row / std_s_row
            signif_s_col = mean_s_col / std_s_col
            signif_p_row = mean_p_row / std_p_row
            signif_p_col = mean_p_col / std_p_col

            ax_mean_i_row.plot(xrow_i, mean_i_row)
            ax_mean_i_col.plot(xcol_i, mean_i_col)
            ax_mean_s_row.plot(xrow_s, mean_s_row)
            ax_mean_s_col.plot(xcol_s, mean_s_col)
            ax_mean_p_row.plot(xrow_p, mean_p_row)
            ax_mean_p_col.plot(xcol_p, mean_p_col)

            ax_std_i_row.plot(xrow_i, std_i_row)
            ax_std_i_col.plot(xcol_i, std_i_col)
            ax_std_s_row.plot(xrow_s, std_s_row)
            ax_std_s_col.plot(xcol_s, std_s_col)
            ax_std_p_row.plot(xrow_p, std_p_row)
            ax_std_p_col.plot(xcol_p, std_p_col)

            ax_signif_i_row.plot(xrow_i, signif_i_row)
            ax_signif_i_col.plot(xcol_i, signif_i_col)
            ax_signif_s_row.plot(xrow_s, signif_s_row)
            ax_signif_s_col.plot(xcol_s, signif_s_col)
            ax_signif_p_row.plot(xrow_p, signif_p_row)
            ax_signif_p_col.plot(xcol_p, signif_p_col)

        outbase = os.path.join("superbias", "plots", "%s_%s_%s" % (raft, run_num, slot))

        if bias_type is None:
            outbase += "_b-none"
        else:
            outbase += "_b-%s" % bias_type

        if superbias_type is None:
            outbase += "_s-none"
        else:
            outbase += "_s-%s" % superbias_type

        fig_mean_i_row.savefig("%s_mean_stack_i_row.png" % outbase)
        fig_mean_i_col.savefig("%s_mean_stack_i_col.png" % outbase)
        fig_mean_s_row.savefig("%s_mean_stack_s_row.png" % outbase)
        fig_mean_s_col.savefig("%s_mean_stack_s_col.png" % outbase)
        fig_mean_p_row.savefig("%s_mean_stack_p_row.png" % outbase)
        fig_mean_p_col.savefig("%s_mean_stack_p_col.png" % outbase)

        fig_std_i_row.savefig("%s_std_stack_i_row.png" % outbase)
        fig_std_i_col.savefig("%s_std_stack_i_col.png" % outbase)
        fig_std_s_row.savefig("%s_std_stack_s_row.png" % outbase)
        fig_std_s_col.savefig("%s_std_stack_s_col.png" % outbase)
        fig_std_p_row.savefig("%s_std_stack_p_row.png" % outbase)
        fig_std_p_col.savefig("%s_std_stack_p_col.png" % outbase)

        fig_signif_i_row.savefig("%s_signif_stack_i_row.png" % outbase)
        fig_signif_i_col.savefig("%s_signif_stack_i_col.png" % outbase)
        fig_signif_s_row.savefig("%s_signif_stack_s_row.png" % outbase)
        fig_signif_s_col.savefig("%s_signif_stack_s_col.png" % outbase)
        fig_signif_p_row.savefig("%s_signif_stack_p_row.png" % outbase)
        fig_signif_p_col.savefig("%s_signif_stack_p_col.png" % outbase)




def run_plot_oscan_correl(raftName, run_num, **kwargs):
    """Plot the correlations between the serial overscan for each amp on a raft

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'

    Keyword arguments
    -----------------
    covar:       bool
    root_dir:    str
    rtype:       str
    """

    covar = kwargs.get('covar', False)
    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)
    rtype = kwargs.get('rtype', 'raft')

    if rtype == 'raft':
        bias_files = get_bias_files_raft(raftName, run_num,
                                         root_data_path=root_dir)
    elif rtype == 'RD':
        bias_files = get_bias_files_RandD(raftName, run_num,
                                          root_data_path=root_dir)

    title = 'Raft {}, {}'.format(raftName, run_num)
    fig = raft_level_oscan_correlations(bias_files, title=title, covar=covar)
    if covar:
        outfile = os.path.join("bias_results", "plots",
                               '{}_{}_overscan_covar.png'.format(raftName, run_num))
    else:
        outfile = os.path.join("bias_results", "plots",
                               '{}_{}_overscan_correlations.png'.format(raftName, run_num))
    fig[0].savefig(outfile)



def run_plot_superbias_fft(raft, run_num, slot_list, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a superbias frame

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_list:   list
       List of slots

    Keyword arguments
    -----------------
    mask_types:     list
    root_dir:       string
    mask:           bool
    std:            bool
    superbias:      str
    """
    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)
    mask_types = kwargs.get('mask_types', MASK_TYPES_DEFAULT)
    mask = kwargs.get('mask', False)
    std = kwargs.get('std', False)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
 
    # If we are doing more that one slot, don't show the plots
    if len(slot_list) > 1:
        plt.ioff()
    else:
        plt.ion()

    for slot in slot_list:
        superbias_file = os.path.join('superbias',
                                      '%s-%s-%s_superbias_b-%s.fits' %\
                                          (raft, run_num, slot, superbias_type))

        if mask:
            sensor_id = (os.path.splitext(os.path.split(superbias_file)[-1])[0]).split('_')[0]
            mask_files = get_mask_files_slot(raft, run_num, sensor_id, mask_types, root_dir)
        else:
            mask_files = []

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

        fig_raw_i_row, axs_raw_i_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_s_row, axs_raw_s_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_p_row, axs_raw_p_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))


        for i, amp in enumerate(superbias):

            image = superbias[amp]
            frames = get_image_frames_2d(image, oscan)

            i_struct = array_struct(frames['i_array']-frames['i_array'].mean(), do_std=std)
            s_struct = array_struct(frames['s_array']-frames['s_array'].mean(), do_std=std)
            p_struct = array_struct(frames['p_array']-frames['p_array'].mean(), do_std=std)

            fftpow_i = np.abs(fftpack.fft(i_struct['rows']))
            fftpow_s = np.abs(fftpack.fft(s_struct['rows']))
            fftpow_p = np.abs(fftpack.fft(p_struct['rows']))

            fftpow_i /= len(fftpow_i)/2
            fftpow_s /= len(fftpow_s)/2
            fftpow_p /= len(fftpow_p)/2

            plot_fft(axs_raw_i_row.flat[i], freqs_i, fftpow_i)
            plot_fft(axs_raw_s_row.flat[i], freqs_s, fftpow_s)
            plot_fft(axs_raw_p_row.flat[i], freqs_p, fftpow_p)


        outbase = os.path.join("superbias", "plots", '%s-%s-%s_superbias' % (raft, run_num, slot))
        outbase += "_b-%s" % superbias_type
        if std:
            outbase += "_std"

        fig_raw_i_row.savefig("%s_fft_i_row.png" % outbase)
        fig_raw_s_row.savefig("%s_fft_s_row.png" % outbase)
        fig_raw_p_row.savefig("%s_fft_p_row.png" % outbase)


def run_plot_superbias_struct(raft, run_num, slot_list, **kwargs):
    """Plot the row-wise and col-wise struture  in a superbias frame

    Parameters
    ----------
    raft:        str
       The raft name, i.e., 'RTM-004-Dev'
    run_num:     str
       The run number, i.e,. '6106D'
    slot_list:   list
       List of slots

    Keyword arguments
    -----------------
    mask_types:     list
    root_dir:       string
    mask:           bool
    std:            bool
    superbias:      str
    """

    root_dir = kwargs.get('root_dir', RAFT_ROOT_FOLDER)
    mask_types = kwargs.get('mask_types', MASK_TYPES_DEFAULT)
    mask = kwargs.get('mask', False)
    std = kwargs.get('std', False)
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)

    for slot in slot_list:
        superbias_file = os.path.join('superbias',
                                      '%s-%s-%s_superbias_b-%s.fits' %\
                                          (raft, run_num, slot, superbias_type))

        if mask:
            sensor_id = (os.path.splitext(os.path.split(superbias_file)[-1])[0]).split('_')[0]
            mask_files = get_mask_files_slot(raft, run_num, sensor_id, mask_types, root_dir)
        else:
            mask_files = []

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

        fig_raw_i_row, axs_raw_i_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_i_col, axs_raw_i_col = setup_amp_plots_grid("col", "counts", figsize=(15, 10))
        fig_raw_s_row, axs_raw_s_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_s_col, axs_raw_s_col = setup_amp_plots_grid("col", "counts", figsize=(15, 10))
        fig_raw_p_row, axs_raw_p_row = setup_amp_plots_grid("row", "counts", figsize=(15, 10))
        fig_raw_p_col, axs_raw_p_col = setup_amp_plots_grid("col", "counts", figsize=(15, 10))

        for i, amp in enumerate(superbias):

            image = superbias[amp]
            frames = get_image_frames_2d(image, oscan)

            i_struct = array_struct(frames['i_array'], do_std=std)
            s_struct = array_struct(frames['s_array'], do_std=std)
            p_struct = array_struct(frames['p_array'], do_std=std)

            ax_raw_i_row = axs_raw_i_row.flat[i]
            ax_raw_i_col = axs_raw_i_col.flat[i]
            ax_raw_s_row = axs_raw_s_row.flat[i]
            ax_raw_s_col = axs_raw_s_col.flat[i]
            ax_raw_p_row = axs_raw_p_row.flat[i]
            ax_raw_p_col = axs_raw_p_col.flat[i]

            ax_raw_i_row.plot(xrow_i, i_struct['rows'])
            ax_raw_i_col.plot(xcol_i, i_struct['cols'])
            ax_raw_s_row.plot(xrow_s, s_struct['rows'])
            ax_raw_s_col.plot(xcol_s, s_struct['cols'])
            ax_raw_p_row.plot(xrow_p, p_struct['rows'])
            ax_raw_p_col.plot(xcol_p, p_struct['cols'])

        outbase = os.path.join("superbias", "plots", '%s-%s-%s_superbias' % (raft, run_num, slot))
        outbase += "_b-%s" % superbias_type
        if std:
            outbase += "_std"


        fig_raw_i_row.savefig("%s_i_row.png" % outbase)
        fig_raw_i_col.savefig("%s_i_col.png" % outbase)
        fig_raw_s_row.savefig("%s_s_row.png" % outbase)
        fig_raw_s_col.savefig("%s_s_col.png" % outbase)
        fig_raw_p_row.savefig("%s_p_row.png" % outbase)
        fig_raw_p_col.savefig("%s_p_col.png" % outbase)
