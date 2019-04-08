"""Functions to analyse bias and superbias frames"""

from lsst.eo_utils.base.plot_utils import FigureDict


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


def plot_bias_data_slot(dtables, figs):
    """Plot the all the bias data
    @param dtables (TableDict)  The data
    @param figs (FigureDict)    Object to store the figues
    """
    plot_bias_v_row_slot(dtables, figs)
    plot_bias_fft_slot(dtables, figs)
    plot_bias_struct_slot(dtables, figs)
    plot_correl_wrt_oscan_slot(dtables, figs)
    plot_oscan_amp_stack_slot(dtables, figs)


def plot_superbias_stats_raft(dtables, figs):
    """Plot the bias fft

    @param dtables (TableDict)  The data
    @param figs (FigureDict)    Object to store the figues
    """
    data = dtables.get_table('stats')

    figs.plot_stat_color("mean", data['mean'], clabel="Mean of STD [ADU]")
    figs.plot_stat_color("std", data['std'], clabel="STD of STD [ADU]")
