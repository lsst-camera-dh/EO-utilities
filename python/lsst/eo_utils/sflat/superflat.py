"""Class to construct superbias frames"""

import os

import numpy as np

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.file_utils import makedir_safe

from lsst.eo_utils.base.butler_utils import get_filename_from_id

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.image_utils import flip_data_in_place,\
    sort_sflats, stack_images, extract_raft_array_dict,\
    outlier_raft_dict, fill_footprint_dict, extract_raft_imaging_data,\
    extract_raft_unbiased_images

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.merge_utils import CameraMosaicConfig, CameraMosaicTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .file_utils import SUPERFLAT_FORMATTER, SUPERFLAT_SPEC_FORMATTER, RUN_SUPERFLAT_FORMATTER

from .analysis import SflatAnalysisConfig,\
    SflatAnalysisTask

from .meta_analysis import SflatRaftTableAnalysisConfig,\
    SflatRaftTableAnalysisTask


class SuperflatConfig(SflatAnalysisConfig):
    """Configuration for SuperflatTask"""
    stat = EOUtilOptions.clone_param('stat')
    bitpix = EOUtilOptions.clone_param('bitpix')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    filekey = EOUtilOptions.clone_param('filekey')


class SuperflatTask(SflatAnalysisTask):
    """Construct superflat frames"""

    ConfigClass = SuperflatConfig
    _DefaultName = "SuperflatTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SUPERFLAT_FORMATTER

    plot_names = ['img_l', 'img_h', 'img_r',
                  'hist_l', 'hist_h', 'hist_r']

    # Used to distinguish low from high flats in butlerized data
    exptime_cut = 20.

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        super().__init__(**kwargs)
        self._superflat_frame_l = None
        self._superflat_frame_h = None
        self._superflat_frame_r = None


    def extract(self, butler, data, **kwargs):
        """Make superflat frame for one slot

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
        sflat_l : `dict`
            Dictionary keyed by amp of the low exposure superflats
        sflat_h : `dict`
            Dictionary keyed by amp of the high exposure superflats
        ratio_images : `dict`
            Dictionary keyed by amp of the low/high ratio images
        """
        self.safe_update(**kwargs)
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE
        bias_type = self.get_bias_algo()
        bias_type_col = self.get_bias_col_algo()

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        gains = self.get_gains()
        nlc = self.get_nonlinearirty_correction()

        sflat_files = data['SFLAT']

        if not sflat_files:
            self.log_warn_slot_msg(self.config, "No superflat files")
            return None

        sflat_files_l, sflat_files_h = sort_sflats(butler, sflat_files, self.exptime_cut)

        if not sflat_files_l:
            self.log_warn_slot_msg(self.config, "No lo superflat files")
            return None
        if not sflat_files_h:
            self.log_warn_slot_msg(self.config, "No hi superflat files")
            return None

        self.log_info_slot_msg(self.config, "%i %i %i files" % (len(sflat_files),
                                                                len(sflat_files_l),
                                                                len(sflat_files_h)))



        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        sflat_l = stack_images(butler, sflat_files_l, statistic=statistic,
                               bias_type=bias_type, bias_type_col=bias_type_col,
                               superbias_frame=superbias_frame,
                               gains=gains,
                               nlc=nlc)
        sflat_h = stack_images(butler, sflat_files_h, statistic=statistic,
                               bias_type=bias_type, bias_type_col=bias_type_col,
                               superbias_frame=superbias_frame,
                               gains=gains,
                               nlc=nlc)

        ratio_images = {}
        for amp in range(1, 17):
            im_l = sflat_l[amp]
            im_h = sflat_h[amp]
            ratio = im_l.array / im_h.array
            ratio_images[amp] = afwImage.ImageF(ratio)

        self.log_progress("Done!")
        return (sflat_l, sflat_h, ratio_images)


    def make_superflats(self, butler, data, **kwargs):
        """Stack the input data to make superflat frames

        The superflats are stored as data members of this class

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

        mask_files = self.get_mask_files()

        output_file = self.tablefile_name()
        makedir_safe(output_file)


        if not self.config.skip:
            sflats = self.extract(butler, data)
            if sflats is None:
                return

            if butler is None:
                template_file = data['SFLAT'][0]
            else:
                template_file = get_filename_from_id(butler, data['SFLAT'][0])

            imutil.writeFits(sflats[0], output_file + '_l.fits',
                             template_file, self.config.bitpix)
            imutil.writeFits(sflats[1], output_file + '_h.fits',
                             template_file, self.config.bitpix)
            imutil.writeFits(sflats[2], output_file + '_r.fits',
                             template_file, self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file + '_l.fits')
                flip_data_in_place(output_file + '_h.fits')
                flip_data_in_place(output_file + '_r.fits')

        self._superflat_frame_l = self.get_ccd(None, output_file + '_l.fits', mask_files)
        self._superflat_frame_h = self.get_ccd(None, output_file + '_h.fits', mask_files)
        self._superflat_frame_r = self.get_ccd(None, output_file + '_r.fits', mask_files)


    def plot(self, dtables, figs, **kwargs):
        """Make plots of the pixel-by-pixel distributions
        of the superflat frames

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

        if dtables is not None:
            raise ValueError("dtables should not be set in SuperflatTask.plot")

        if self._superflat_frame_l is None:
            return

        if self.config.plot:
            figs.plot_sensor("img_l", self._superflat_frame_l)
            figs.plot_sensor("img_h", self._superflat_frame_h)
            figs.plot_sensor("img_r", self._superflat_frame_r)

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.extract_config_vals(default_array_kw)
            figs.histogram_array("hist_l", self._superflat_frame_l,
                                 title="Historam of RMS of flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, bins=100, range=(0., 2000,),
                                 **kwcopy)
            figs.histogram_array("hist_h", self._superflat_frame_h,
                                 title="Historam of RMS of flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, bins=100, range=(0., 100000,),
                                 **kwcopy)
            figs.histogram_array("hist_r", self._superflat_frame_r,
                                 title="Historam of Ratio flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.02",
                                 subtract_mean=False, bins=100, range=(0.015, 0.025),
                                 **kwcopy)

    def plotfile_name(self, **kwargs):
        """Get the basename for the plot files for a particular run, raft, ccd...

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The name of the file
        """
        self.safe_update(**kwargs)
        return self.get_superflat_file('').replace('.fits', '')


    def __call__(self, butler, data, **kwargs):
        """Tie together analysis functions

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)
        self.make_superflats(butler, data)
        if self.config.plot is not None:
            self.make_plots(None)



class SuperflatRaftConfig(SflatRaftTableAnalysisConfig):
    """Configuration for FlatSuperflatRaftTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='sflat')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    mosaic = EOUtilOptions.clone_param('mosaic')


class SuperflatRaftTask(SflatRaftTableAnalysisTask):
    """Analyze the correlations between the overscans for all amplifiers on a raft"""

    ConfigClass = SuperflatRaftConfig
    _DefaultName = "SuperflatRaftTask"

    intablename_format = SUPERFLAT_FORMATTER

    plot_names = ['mosaic_l', 'stats_l', 'l_out-row', 'l_out-col', 'l_nbad', 'l_nbad-row', 'l_nbad-col',
                  'mosaic_l', 'stats_h', 'h_out-row', 'h_out-col', 'h_nbad', 'h_nbad-row', 'h_nbad-col',
                  'mosaic_r', 'stats_r', 'r_out-row', 'r_out-col', 'r_nbad', 'r_nbad-row', 'r_nbad-col']

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SflatRaftTableAnalysisTask.__init__(self, **kwargs)
        self._mask_file_dict = {}
        self._sflat_file_dict_l = {}
        self._sflat_file_dict_h = {}
        self._sflat_file_dict_r = {}
        self._sflat_images_h = None
        self._sflat_array_l = None
        self._sflat_array_h = None
        self._sflat_array_r = None


    @staticmethod
    def build_defect_dict(flat_array, **kwargs):
        """Extract information about the defects into a dictionary

        Parameters
        ----------
        flat_array : `dict`
            The images, keyed by slot, amp
        kwargs
            Used to override default configuration

        Returns
        -------
        out_dict : `dict`
            The output dictionary
        """
        fp_dict = dict(slot=[],
                       amp=[],
                       x_corner=[],
                       y_corner=[],
                       x_peak=[],
                       y_peak=[],
                       x_size=[],
                       y_size=[],
                       ratio_full=[])
        for i in range(4):
            fp_dict['ratio_%i' % i] = []
            fp_dict['npix_%i' % i] = []
            fp_dict['npix_0p2_%i' % i] = []

        for islot, (_, slot_data) in enumerate(sorted(flat_array.items())):
            for iamp, (_, image) in enumerate(sorted(slot_data.items())):
                image *= -1
                fill_footprint_dict(image.image, fp_dict, iamp, islot, **kwargs)
        return fp_dict


    def extract(self, butler, data, **kwargs):
        """Extract the outliers in the superflat frames for the raft

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

        self._mask_file_dict = {}
        self._sflat_file_dict_l = {}
        self._sflat_file_dict_h = {}
        self._sflat_file_dict_r = {}

        if butler is not None:
            self.log.warn("Ignoring butler")

        self.set_local_data(butler, data, **kwargs)

        if not self._sflat_file_dict_l:
            self.log.warn("No files for %s, skipping" % (self.config.raft))
            return None

        self._sflat_images_h, ccd_dict = extract_raft_unbiased_images(self._sflat_file_dict_h,
                                                                      mask_dict=self._mask_file_dict)
        self._sflat_array_l = extract_raft_array_dict(self._sflat_file_dict_l,
                                                      mask_dict=self._mask_file_dict)
        self._sflat_array_h = extract_raft_imaging_data(self._sflat_images_h,
                                                        ccd_dict)
        self._sflat_array_r = extract_raft_array_dict(self._sflat_file_dict_r,
                                                      mask_dict=self._mask_file_dict)
        out_data_l = outlier_raft_dict(self._sflat_array_l, 1000., 300.)
        out_data_h = outlier_raft_dict(self._sflat_array_h, 50000., 15000.)
        out_data_r = outlier_raft_dict(self._sflat_array_r, 0.019, 0.002)

        fp_dict = SuperflatRaftTask.build_defect_dict(self._sflat_images_h, frac_thresh=0.9)

        dtables = TableDict()
        dtables.make_datatable('defects', fp_dict)
        dtables.make_datatable('outliers_l', out_data_l)
        dtables.make_datatable('outliers_h', out_data_h)
        dtables.make_datatable('outliers_r', out_data_r)
        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Plot the raft-level mosaic and histrograms
        of the numbers of outliers in the superflat frames

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

        figs.make_raft_outlier_plots(dtables['outliers_l'], 'l_')
        figs.make_raft_outlier_plots(dtables['outliers_h'], 'h_')
        figs.make_raft_outlier_plots(dtables['outliers_r'], 'r_')

        if self.config.skip:
            return

        if self.config.mosaic:
            figs.plot_raft_mosaic('mosaic_l', self._sflat_file_dict_l, bias_subtract=False)
            figs.plot_raft_mosaic('mosaic_h', self._sflat_file_dict_h, bias_subtract=False)
            figs.plot_raft_mosaic('mosaic_r', self._sflat_file_dict_r, bias_subtract=False)

        if self.config.stats_hist:
            figs.histogram_raft_array('stats_l', self._sflat_array_l,
                                      xlabel='Counts [ADU]',
                                      ylabel='Pixels',
                                      bins=100,
                                      range=(0., 2000.),
                                      histtype='step')
            figs.histogram_raft_array('stats_h', self._sflat_array_h,
                                      xlabel='Counts [ADU]',
                                      ylabel='Pixels',
                                      bins=100,
                                      range=(0., 100000.),
                                      histtype='step')
            figs.histogram_raft_array('stats_r', self._sflat_array_r,
                                      xlabel='Ratio low/high',
                                      ylabel='Pixels',
                                      bins=np.linspace(0.015, 0.025, 101),
                                      histtype='step')


    def set_local_data(self, butler, data, **kwargs):
        """Set local data members if extract fails

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)

        slots = self.config.slots
        if slots is None:
            slots = ALL_SLOTS

        for slot in slots:
            basename = data[slot]
            if not os.path.exists(basename.replace('.fits', '_l.fits')):
                self.log.warn("Skipping %s:%s" % (self.config.raft, slot))
                continue
            self._mask_file_dict[slot] = self.get_mask_files(slot=slot)
            self._sflat_file_dict_l[slot] = basename.replace('.fits', '_l.fits')
            self._sflat_file_dict_h[slot] = basename.replace('.fits', '_h.fits')
            self._sflat_file_dict_r[slot] = basename.replace('.fits', '_r.fits')



class SuperflatMosaicConfig(CameraMosaicConfig):
    """Configuration for SuperbiasMosaicTask"""

class SuperflatMosaicTask(CameraMosaicTask):
    """Make a mosaic from a superbias frames"""

    ConfigClass = SuperflatMosaicConfig
    _DefaultName = "SuperflatMosaicTask"

    intablename_format = SUPERFLAT_SPEC_FORMATTER
    tablename_format = RUN_SUPERFLAT_FORMATTER
    plotname_format = RUN_SUPERFLAT_FORMATTER

    datatype = 'superflat'



EO_TASK_FACTORY.add_task_class('Superflat', SuperflatTask)
EO_TASK_FACTORY.add_task_class('SuperflatRaft', SuperflatRaftTask)
EO_TASK_FACTORY.add_task_class('SuperflatMosaic', SuperflatMosaicTask)
