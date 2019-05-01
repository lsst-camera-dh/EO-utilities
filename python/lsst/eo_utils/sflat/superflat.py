"""Class to construct superbias frames"""

import sys

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.file_utils import makedir_safe

from lsst.eo_utils.base.defaults import SFLAT_TEMPLATE,\
    DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    flip_data_in_place, sort_sflats, stack_images

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.sflat.analysis import SflatAnalysisConfig,\
    SflatAnalysisTask


class SuperflatConfig(SflatAnalysisConfig):
    """Configuration for SuperflatTask"""
    mask = EOUtilOptions.clone_param('mask')
    stat = EOUtilOptions.clone_param('stat')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    bitpix = EOUtilOptions.clone_param('bitpix')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')


class SuperflatTask(SflatAnalysisTask):
    """Construct superflat frames"""

    ConfigClass = SuperflatConfig
    _DefaultName = "SuperflatTask"
    iteratorClass = AnalysisBySlot


    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        SflatAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Make superflat frame for one slot

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the flat and mask files
        @param kwargs              Uped to override config
        """
        self.safe_update(**kwargs)
        slot = self.config.slot
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        sflat_files = data['SFLAT']
        sys.stdout.write("Working on %s, %i files.\n" % (slot, len(sflat_files)))

        sflat_files_l, sflat_files_h = sort_sflats(butler, sflat_files)

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        sflat_l = stack_images(butler, sflat_files_l, statistic=statistic,
                               bias_type=self.config.bias, superbias_frame=superbias_frame)
        sflat_h = stack_images(butler, sflat_files_h, statistic=statistic,
                               bias_type=self.config.bias, superbias_frame=superbias_frame)

        ratio_images = {}
        for amp in range(1, 17):
            im_l = sflat_l[amp]
            im_h = sflat_h[amp]
            ratio = im_l.array / im_h.array
            ratio_images[amp] = afwImage.ImageF(ratio)

        return (sflat_l, sflat_h, ratio_images)

    def make_superflats(self, butler, slot_data, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the flat and mask files
        @param kwargs

        @return (dict)
        """
        self.safe_update(**kwargs)

        mask_files = self.get_mask_files()

        output_file = self.get_superflat_file('').replace('.fits', '')
        makedir_safe(output_file)

        if not self.config.skip:
            sflats = self.extract(butler, slot_data)
            imutil.writeFits(sflats[0], output_file + '_l.fits', SFLAT_TEMPLATE, self.config.bitpix)
            imutil.writeFits(sflats[1], output_file + '_h.fits', SFLAT_TEMPLATE, self.config.bitpix)
            imutil.writeFits(sflats[2], output_file + '_ratio.fits', SFLAT_TEMPLATE, self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file + '_l.fits')
                flip_data_in_place(output_file + '_h.fits')
                flip_data_in_place(output_file + '_ratio.fits')

        sflat_l = get_ccd_from_id(None, output_file + '_l.fits', mask_files)
        sflat_h = get_ccd_from_id(None, output_file + '_h.fits', mask_files)
        sflat_ratio = get_ccd_from_id(None, output_file + '_ratio.fits', mask_files)
        return (sflat_l, sflat_h, sflat_ratio)


    def plot(self, sflats, figs, **kwargs):
        """Make plots of the superflat frame

        @param sflat (str)          The superflat frame
        @param figs (`FigureDict`)  Place to collect figures
        @param kwargs:
            plot (bool)              Plot images of the superflat
            stats_hist (bool)        Plot statistics
        """
        self.safe_update(**kwargs)

        subtract_mean = False

        if self.config.plot:
            figs.plot_sensor("img_l", None, sflats[0])
            figs.plot_sensor("img_h", None, sflats[1])
            figs.plot_sensor("ratio", None, sflats[2])

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.extract_config_vals(default_array_kw)
            figs.histogram_array("hist_l", None, sflats[0],
                                 title="Historam of RMS of flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, vmin=0, vmax=2000,
                                 **kwcopy)
            figs.histogram_array("hist_h", None, sflats[1],
                                 title="Historam of RMS of flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, vmin=0, vmax=100000,
                                 **kwcopy)
            figs.histogram_array("hist_ratio", None, sflats[2],
                                 title="Historam of Ratio flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.02",
                                 subtract_mean=False, vmin=0.0, vmax=0.2,
                                 **kwcopy)



    def make_plots(self, sflat, **kwargs):
        """Tie together the functions to make the data tables
        @param sflat (`MaskedCCD`)   The superflat frame

        @return (`FigureDict`) the figues we produced
        """
        self.safe_update(**kwargs)

        figs = FigureDict()
        self.plot(sflat, figs)
        if self.config.plot == 'display':
            figs.save_all(None)
            return figs

        plotbase = self.get_superflat_file('').replace('.fits', '')

        makedir_safe(plotbase)
        figs.save_all(plotbase, self.config.plot)
        return None


    def __call__(self, butler, slot_data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the flat and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        self.safe_update(**kwargs)
        sflats = self.make_superflats(butler, slot_data)
        if self.config.plot is not None:
            self.make_plots(sflats)


EO_TASK_FACTORY.add_task_class('Superflat', SuperflatTask)
