"""Class to analyze the FFT of the bias frames"""

import sys

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_dims_from_ccd,\
    get_raw_image, get_geom_regions, get_amp_list

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.sflat.file_utils import SLOT_SFLAT_TABLE_FORMATTER,\
    RAFT_SFLAT_TABLE_FORMATTER, RAFT_SFLAT_PLOT_FORMATTER

from lsst.eo_utils.sflat.analysis import SflatAnalysisConfig, SflatAnalysisTask


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
        self.low_images = {}
        self.high_images = {}
        self.ratio_images = {}
        self.superbias_images = {}
        self.quality_masks = {}

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
        data_dict = dict(row=row_data_dict,
                         col=col_data_dict,
                         amp=amp_data_dict)

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

            self.low_images[i] = l_im[imaging].array
            self.high_images[i] = h_im[imaging].array
            self.ratio_images[i] = ratio_im[imaging].array
            self.superbias_images[i] = superbias_im[imaging].array

            quality_mask = np.zeros(self.superbias_images[i].shape)
            quality_mask += 1. * np.invert(np.fabs(self.superbias_images[i]) < 10)
            quality_mask += 2. * np.invert(np.fabs(self.ratio_images[i] - 0.020) < 0.0015)
            self.quality_masks[i] = quality_mask

            row_data_dict['row_i'] = np.linspace(0, dims['nrow_i']-1, dims['nrow_i'])
            row_data_dict['l_med_%s_a%02i' % (slot, i)] = np.median(self.low_images[i], 1)
            row_data_dict['h_med_%s_a%02i' % (slot, i)] = np.median(self.high_images[i], 1)
            row_data_dict['r_med_%s_a%02i' % (slot, i)] = np.median(self.ratio_images[i], 1)
            if superbias_im is not None:
                row_data_dict['sbias_med_%s_a%02i' % (slot, i)] =\
                    np.median(self.superbias_images[i], 1)

            col_data_dict['col_i'] = np.linspace(0, dims['ncol_i']-1, dims['ncol_i'])
            col_data_dict['l_med_%s_a%02i' % (slot, i)] = np.median(self.low_images[i], 0)
            col_data_dict['h_med_%s_a%02i' % (slot, i)] = np.median(self.high_images[i], 0)
            col_data_dict['r_med_%s_a%02i' % (slot, i)] = np.median(self.ratio_images[i], 0)
            if superbias_im is not None:
                col_data_dict['sbias_med_%s_a%02i' % (slot, i)] =\
                    np.median(self.superbias_images[i], 0)

            amp_data_dict['l_med_%s_a%02i' % (slot, i)] = [np.median(self.low_images[i])]
            amp_data_dict['h_med_%s_a%02i' % (slot, i)] = [np.median(self.high_images[i])]
            amp_data_dict['r_med_%s_a%02i' % (slot, i)] = [np.median(self.ratio_images[i])]


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

        figs.plot_amp_arrays("mask", self.quality_masks, vmin=0, vmax=3)

        for i in range(16):
            figs.plot_two_image_hist2d('scatter', i,
                                       self.superbias_images[i],
                                       self.ratio_images[i],
                                       bins=(200, 200),
                                       range=((-50, 50.), (0.018, 0.022)))



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
