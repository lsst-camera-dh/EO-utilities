"""Functions to analyse bias and superbias frames"""

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES, REGION_LABELS


ALL_SLOTS = 'S00 S01 S02 S10 S11 S12 S20 S21 S22'.split()


def plot_superbias(output_file, mask_files, **kwargs):
    """Make plots of the superbias frame

    @param output_file (str)    File with the superbias frame
    @param mask_files (list)    Bad pixels masks
    @param kwargs:
       plot (bool)              Plot images of the superbias
       stats_hist (bool)        Plot statistics
    """
    figs = FigureDict()


    if kwargs.get('plot', False):
        figs.plot_sensor("img", output_file, mask_files)

    if kwargs.get('stats_hist', False):
        kwcopy = kwargs.copy()
        kwcopy.pop('bias', None)
        kwcopy.pop('superbias', None)
        figs.histogram_array("hist", output_file, mask_files,
                             title="Historam of RMS of bias-images, per pixel",
                             xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                             **kwcopy)

    figs.save_all(output_file.replace('.fits', ''))



def plot_bias_v_row_slot(dtables, outbase):
    """Plot the bias as function of row

    @param dtables (TableDict)  The data
    @param outbase (str)        The output file prefix
    """
    figs = FigureDict()
    figs.setup_amp_plots_grid("biasval", title="Bias by row",
                              xlabel="row", ylabel="Magnitude [ADU]")
    figs.plot_xy_amps_from_tabledict(dtables, 'biasval', 'biasval',
                                     x_name='row_s', y_name='biasval')
    figs.save_all(outbase)


def plot_bias_fft_slot(dtables, outbase):
    """Plot the bias fft

    @param dtables (TableDict)  The data
    @param outbase (str)        The output file prefix
    """
    figs = FigureDict()
    for key, region in zip(REGION_KEYS, REGION_NAMES):
        datakey = 'biasfft-%s' % key
        figs.setup_amp_plots_grid(datakey, title="FFT of %s region mean by row" % region,
                                  xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
        figs.plot_xy_amps_from_tabledict(dtables, datakey, datakey,
                                         x_name='freqs', y_name='fftpow')
    figs.save_all(outbase)


def plot_bias_struct_slot(dtables, outbase):
    """Plot the bias structure

    @param dtables (TableDict)  The data
    @param outbase (str)        The output file prefix
    """
    figs = FigureDict()
    for rkey, rlabel in zip(REGION_KEYS, REGION_LABELS):
        for dkey in ['row', 'col']:
            datakey = "biasst-%s_%s" % (dkey, rkey)
            figs.setup_amp_plots_grid(datakey, title="%s, profile by %s" % (rlabel, dkey),
                                      xlabel=dkey, ylabel="ADU")
            figs.plot_xy_amps_from_tabledict(dtables, datakey, datakey,
                                             x_name="%s_%s" % (dkey, rkey), y_name="biasst")
    figs.save_all(outbase)


def plot_correl_wrt_oscan_slot(dtables, outbase):
    """Plot the bias fft

    @param dtables (TableDict)  The data
    @param outbase (str)        The output file prefix
    """
    figs = FigureDict()

    figs.setup_amp_plots_grid("oscorr-row", title="Correlation: imaging region and serial overscan",
                              xlabel="Correlation",
                              ylabel="Number of frames")
    figs.setup_amp_plots_grid("oscorr-col", title="Correlation: imaging region and paralell overscan",
                              xlabel="Correlation",
                              ylabel="Number of frames")

    df = dtables.get_table("correl")
    for i in range(16):
        s_correl = df['s_correl_a%02i' % i]
        p_correl = df['p_correl_a%02i' % i]
        figs.get_obj('oscorr-row', 'axs').flat[i].hist(s_correl, bins=100, range=(-1., 1.))
        figs.get_obj('oscorr-col', 'axs').flat[i].hist(p_correl, bins=100, range=(-1., 1.))
    figs.save_all(outbase)


def plot_oscan_amp_stack_slot(dtables, outbase):
    """Plot the bias structure

    @param dtables (TableDict)  The data
    @param outbase (str)        The output file prefix
    """
    figs = FigureDict()
    stats = ['mean', 'std', 'signif']
    stats_labels = ['Mean [ADU]', 'Std [ADU]', 'Significance [sigma]']
    for skey, slabel in zip(stats, stats_labels):
        y_name = "stack_%s" % skey
        figkey = "biasosstack-%s" % skey
        figs.setup_region_plots_grid(figkey, title=stats,
                                     xlabel="Channel", ylabel=slabel)

        idx = 0
        for rkey in REGION_KEYS:
            for dkey in ['row', 'col']:
                xkey = "%s_%s" % (dkey, rkey)
                datakey = "stack-%s" % xkey
                figs.plot_xy_axs_from_tabledict(dtables, datakey, idx, figkey,
                                                x_name=xkey, y_name=y_name)
                idx += 1
    figs.save_all(outbase)


def plot_oscan_correl_raft(dtables, outbase):
    """Plot the bias fft

    @param dtables (TableDict)  The data
    @param outbase (str)        The output file prefix
    """
    figs = FigureDict()

    data = dtables.get_table('correl')['correl']

    figs.plot_raft_correl_matrix("oscorr", data, title="Overscan Correlations", slots=ALL_SLOTS)
    figs.save_all(outbase)
