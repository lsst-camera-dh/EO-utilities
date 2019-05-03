"""Class to construct superbias frames"""

import sys

import numpy as np

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.file_utils import makedir_safe

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    flip_data_in_place, sort_sflats, stack_images, extract_raft_array_dict,\
    outlier_raft_dict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot,\
    AnalysisByRaft

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.sflat.file_utils import RAFT_SFLAT_TABLE_FORMATTER,\
    RAFT_SFLAT_PLOT_FORMATTER

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
        self._superflat_frame_l = None
        self._superflat_frame_h = None
        self._superflat_frame_r = None


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
            imutil.writeFits(sflats[0], output_file + '_l.fits',
                             slot_data['SFLAT'][0], self.config.bitpix)
            imutil.writeFits(sflats[1], output_file + '_h.fits',
                             slot_data['SFLAT'][0], self.config.bitpix)
            imutil.writeFits(sflats[2], output_file + '_ratio.fits',
                             slot_data['SFLAT'][0], self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file + '_l.fits')
                flip_data_in_place(output_file + '_h.fits')
                flip_data_in_place(output_file + '_ratio.fits')

        self._superflat_frame_l = get_ccd_from_id(None, output_file + '_l.fits', mask_files)
        self._superflat_frame_h = get_ccd_from_id(None, output_file + '_h.fits', mask_files)
        self._superflat_frame_r = get_ccd_from_id(None, output_file + '_ratio.fits', mask_files)
        dtables = TableDict()
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots of the superflat frame

        @param sflat (str)          The superflat frame
        @param figs (`FigureDict`)  Place to collect figures
        @param kwargs:
            plot (bool)              Plot images of the superflat
            stats_hist (bool)        Plot statistics
        """
        self.safe_update(**kwargs)

        if dtables.keys():
            raise ValueError("dtables should not be set")

        if self.config.plot:
            figs.plot_sensor("img_l", None, self._superflat_frame_l)
            figs.plot_sensor("img_h", None, self._superflat_frame_h)
            figs.plot_sensor("ratio", None, self._superflat_frame_r)

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.extract_config_vals(default_array_kw)
            figs.histogram_array("hist_l", None, self._superflat_frame_l,
                                 title="Historam of RMS of flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, bins=100, range=(0., 2000,),
                                 **kwcopy)
            figs.histogram_array("hist_h", None, self._superflat_frame_h,
                                 title="Historam of RMS of flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, bins=100, range=(0., 100000,),
                                 **kwcopy)
            figs.histogram_array("hist_ratio", None, self._superflat_frame_r,
                                 title="Historam of Ratio flat-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.02",
                                 subtract_mean=False, bins=100, range=(0.015, 0.025),
                                 **kwcopy)



    def make_plots(self, dtables, **kwargs):
        """Tie together the functions to make the data tables
        @param sflat (`MaskedCCD`)   The superflat frame

        @return (`FigureDict`) the figues we produced
        """
        self.safe_update(**kwargs)

        figs = FigureDict()
        self.plot(dtables, figs)
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
        dtables = self.make_superflats(butler, slot_data)
        if self.config.plot is not None:
            self.make_plots(dtables)



class SuperflatRaftConfig(SflatAnalysisConfig):
    """Configuration for FlatSuperflatRaftTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='raft')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    mosaic = EOUtilOptions.clone_param('mosaic')


class SuperflatRaftTask(SflatAnalysisTask):
    """Analyze the correlations between the overscans for all amplifiers on a raft"""

    ConfigClass = SuperflatRaftConfig
    _DefaultName = "SuperflatRaftTask"
    iteratorClass = AnalysisByRaft

    tablename_format = RAFT_SFLAT_TABLE_FORMATTER
    plotname_format = RAFT_SFLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor"""
        SflatAnalysisTask.__init__(self, **kwargs)
        self._mask_file_dict = {}
        self._sflat_file_dict_l = {}
        self._sflat_file_dict_h = {}
        self._sflat_file_dict_r = {}
        self._sflat_array_l = None
        self._sflat_array_h = None
        self._sflat_array_r = None

    def extract(self, butler, data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the flat and mask files
        @param kwargs            Used to override configuration

        @returns (TableDict)
        """
        self.safe_update(**kwargs)

        if butler is not None:
            sys.stdout.write("Ignoring butler in extract_superflat_fft_slot\n")
        if data is not None:
            sys.stdout.write("Ignoring raft_data in extract_superflat_fft_raft\n")

        for slot in ALL_SLOTS:
            self._mask_file_dict[slot] = self.get_mask_files(slot=slot)
            basename = self.get_superflat_file('', slot=slot).replace('.fits', '')
            self._sflat_file_dict_l[slot] = basename + '_l.fits'
            self._sflat_file_dict_h[slot] = basename + '_h.fits'
            self._sflat_file_dict_r[slot] = basename + '_ratio.fits'

        self._sflat_array_l = extract_raft_array_dict(None, self._sflat_file_dict_l,
                                                      mask_dict=self._mask_file_dict)
        self._sflat_array_h = extract_raft_array_dict(None, self._sflat_file_dict_h,
                                                      mask_dict=self._mask_file_dict)
        self._sflat_array_r = extract_raft_array_dict(None, self._sflat_file_dict_r,
                                                      mask_dict=self._mask_file_dict)
        out_data_l = outlier_raft_dict(self._sflat_array_l, 1000., 300.)
        out_data_h = outlier_raft_dict(self._sflat_array_h, 50000., 15000.)
        out_data_r = outlier_raft_dict(self._sflat_array_r, 0.019, 0.002)

        dtables = TableDict()
        dtables.make_datatable('outliers_l', out_data_l)
        dtables.make_datatable('outliers_h', out_data_h)
        dtables.make_datatable('outliers_r', out_data_r)
        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Plot the flat fft

        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
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


EO_TASK_FACTORY.add_task_class('Superflat', SuperflatTask)
EO_TASK_FACTORY.add_task_class('SuperflatRaft', SuperflatRaftTask)
