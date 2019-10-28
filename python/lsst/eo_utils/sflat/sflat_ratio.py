"""Tasks to analyze superflat low/high exposure ratios"""

import numpy as np

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_dims_from_ccd,\
    get_raw_image, get_geom_regions, get_amp_list

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.sflat.file_utils import SUPERFLAT_FORMATTER

from .meta_analysis import SflatSlotTableAnalysisConfig,\
    SflatSlotTableAnalysisTask


class SflatRatioConfig(SflatSlotTableAnalysisConfig):
    """Configuration for SflatSflatRatioTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    insuffix = EOUtilOptions.clone_param('insuffix', default='')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='sflatratio')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class SflatRatioTask(SflatSlotTableAnalysisTask):
    """Analysis the ratio of low/high exposure superflats"""

    ConfigClass = SflatRatioConfig
    _DefaultName = "SflatRatio"

    intablename_format = SUPERFLAT_FORMATTER

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SflatSlotTableAnalysisTask.__init__(self, **kwargs)
        self.low_images = {}
        self.high_images = {}
        self.ratio_images = {}
        self.superbias_images = {}
        self.quality_masks = {}

    def extract(self, butler, data, **kwargs):
        """Extract data about the low/high superflat exposure ratios

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        if butler is not None:
            self.log.warn("Ignoring butler")

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)
        superflat_file = data[0]

        l_frame = self.get_ccd(None,
                               superflat_file.replace('_l.fits', '_l.fits'),
                               mask_files)
        h_frame = self.get_ccd(None,
                               superflat_file.replace('_l.fits', '_h.fits'),
                               mask_files)
        ratio_frame = self.get_ccd(None,
                                   superflat_file.replace('_l.fits', '_ratio.fits'),
                                   mask_files)

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

        amps = get_amp_list(ratio_frame)
        for i, amp in enumerate(amps):
            dims = get_dims_from_ccd(ratio_frame)
            regions = get_geom_regions(ratio_frame, amp)
            imaging = regions['imaging']
            l_im = get_raw_image(l_frame, amp).image
            h_im = get_raw_image(h_frame, amp).image
            ratio_im = get_raw_image(ratio_frame, amp).image
            if superbias_frame is not None:
                superbias_im = get_raw_image(superbias_frame, amp).image
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
        """Plot data about the low/high superflat ratios

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
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

        for i, (amp, sbias_image) in enumerate(sorted(self.superbias_images)):
            figs.plot_two_image_hist2d('scatter', i,
                                       sbias_image,
                                       self.ratio_images[amp],
                                       bins=(200, 200),
                                       range=((-50, 50.), (0.018, 0.022)))


EO_TASK_FACTORY.add_task_class('SflatRatio', SflatRatioTask)
