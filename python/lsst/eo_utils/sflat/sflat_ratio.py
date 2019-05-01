"""Class to analyze the FFT of the bias frames"""

import sys

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_dims_from_ccd,\
    get_ccd_from_id, get_raw_image, get_geom_regions, get_amp_list

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.sflat.file_utils import SLOT_SFLAT_TABLE_FORMATTER,\
    RAFT_SFLAT_TABLE_FORMATTER, RAFT_SFLAT_PLOT_FORMATTER

from lsst.eo_utils.sflat.analysis import SflatAnalysisConfig, SflatAnalysisTask


def extract_scatter(img_1, img_2, nbinx, ra_x, nbinsy, ra_y):
    img_1_flat = img_1.array.flatten().clip(ra_x[0], ra_x[1])
    img_2_flat = img_2.array.flatten().clip(ra_y[0], ra_y[1])

    hist = np.histogram2d(img_1_flat, img_2_flat, bins=(nbinx, nbinsy), range=[ra_x, ra_y])
    return hist[0].flat


class SflatRatioConfig(SflatAnalysisConfig):
    """Configuration for SflatSflatRatioTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='sflatratio')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class SflatRatioTask(SflatAnalysisTask):
    """Analyze some sflat data"""

    ConfigClass = SflatRatioConfig
    _DefaultName = "SflatRatio"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor """
        SflatAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the data

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the sflat and mask files
        @param kwargs              Used to override defaults

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        if butler is not None:
            sys.stdout.write("Ignoring butler in extract_superbias_fft_slot\n")
        if data is not None:
            sys.stdout.write("Ignoring raft_data in extract_superbias_fft_raft\n")

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        superflat_frames = self.get_superflat_frames(mask_files)
        l_frame = superflat_frames['l']
        h_frame = superflat_frames['h']
        ratio_frame = superflat_frames['ratio']

        # This is a dictionary of dictionaries to store all the
        # data you extract from the sflat_files
        row_data_dict = {}
        col_data_dict = {}
        amp_data_dict = {}
        scatter_dict = {}
        data_dict = dict(row=row_data_dict,
                         col=col_data_dict,
                         amp=amp_data_dict,
                         scatter=scatter_dict)

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #

        amps = get_amp_list(None, ratio_frame)
        for i, amp in enumerate(amps):
            dims = get_dims_from_ccd(None, ratio_frame)
            regions = get_geom_regions(None, ratio_frame, amp)
            imaging = regions['imaging']
            l_im = get_raw_image(None, l_frame, amp)
            h_im = get_raw_image(None, h_frame, amp)
            ratio_im = get_raw_image(None, ratio_frame, amp)
            if superbias_frame is not None:
                superbias_im = get_raw_image(None, superbias_frame, amp)
            else:
                superbias_im = None
            row_data_dict['row_i'] = np.linspace(0, dims['nrow_i']-1, dims['nrow_i'])
            row_data_dict['l_med_%s_a%02i' % (slot, i)] = np.median(l_im[imaging].array, 1)
            row_data_dict['h_med_%s_a%02i' % (slot, i)] = np.median(h_im[imaging].array, 1)
            row_data_dict['r_med_%s_a%02i' % (slot, i)] = np.median(ratio_im[imaging].array, 1)
            if superbias_im is not None:
                row_data_dict['sbias_med_%s_a%02i' % (slot, i)] = np.median(superbias_im[imaging].array, 1)
                            
            col_data_dict['col_i'] = np.linspace(0, dims['ncol_i']-1, dims['ncol_i'])
            col_data_dict['l_med_%s_a%02i' % (slot, i)] = np.median(l_im[imaging].array, 0)
            col_data_dict['h_med_%s_a%02i' % (slot, i)] = np.median(h_im[imaging].array, 0)
            col_data_dict['r_med_%s_a%02i' % (slot, i)] = np.median(ratio_im[imaging].array, 0)
            if superbias_im is not None:
                col_data_dict['sbias_med_%s_a%02i' % (slot, i)] = np.median(superbias_im[imaging].array, 0)

            amp_data_dict['l_med_%s_a%02i' % (slot, i)] = [np.median(l_im[imaging].array)]
            amp_data_dict['h_med_%s_a%02i' % (slot, i)] = [np.median(h_im[imaging].array)]
            amp_data_dict['r_med_%s_a%02i' % (slot, i)] = [np.median(ratio_im[imaging].array)]

            if superbias_im is not None:
                scatter_dict['rs_%s_a%02i' % (slot, i)] = extract_scatter(superbias_im[imaging], ratio_im[imaging],
                                                                          100, (-10, 10.), 100, (0.018, 0.020))

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key, val in data_dict.items():
            dtables.make_datatable(key, val)

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the data

        @param dtables (`TableDict`)  The data
        @param figs (`FigureDict`)    Object to store the figues
        """
        self.safe_update(**kwargs)

        figs.setup_amp_plots_grid("ratio_row", title="sflat ratio by row",
                                  xlabel="row", ylabel="Ratio")
        figs.plot_xy_amps_from_tabledict(dtables, 'row', 'ratio_row',
                                         x_name='row_i', y_name='r_med')

        figs.setup_amp_plots_grid("ratio_col", title="sflat ratio by col",
                                  xlabel="col", ylabel="Ratio")
        figs.plot_xy_amps_from_tabledict(dtables, 'col', 'ratio_col',
                                         x_name='col_i', y_name='r_med')

        figs.setup_amp_plots_grid("scatter", title="sflat ratio v. sbias",
                                  xlabel="Superbias [ADU]", ylabel="Ratio")
        for i in range(16):
            axs = figs.get_amp_axes('scatter', i)
            flat_data = dtables['scatter']['rs_%s_a%02i' % (self.config.slot, i)]
            axs.imshow(flat_data.reshape(100, 100).T, origin='low')



class SflatRatioStatsConfig(SflatAnalysisConfig):
    """Configuration for SflatSlotTempalteStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='sflatratio')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='sflatratio_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class SflatRatioStatsTask(SflatAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = SflatRatioStatsConfig
    _DefaultName = "SflatRatioStatsTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_SFLAT_TABLE_FORMATTER
    tablename_format = RAFT_SFLAT_TABLE_FORMATTER
    plotname_format = RAFT_SFLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor """
        SflatAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract the data

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the sflat and mask files
        @param kwargs              Used to override defaults

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        # You should expand this to include space for the data you want to extract
        data_dict = dict(slot=[],
                         amp=[])

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace(self.config.outsuffix, self.config.insuffix)

            dtables = TableDict(datapath)

            for amp in range(16):

                # Here you can get the data out for each amp and append it to the
                # data_dict

                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("sflatratio", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the sflat fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs




EO_TASK_FACTORY.add_task_class('SflatRatio', SflatRatioTask)
EO_TASK_FACTORY.add_task_class('SflatRatioStats', SflatRatioStatsTask)
