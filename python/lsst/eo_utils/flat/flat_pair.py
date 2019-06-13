"""Class to analyze the FFT of the bias frames"""

import sys

import operator

import numpy as np

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_amp_list,\
    get_exposure_time, get_mondiode_val, get_geom_regions, get_raw_image, unbias_amp

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig, FlatAnalysisTask


class FlatPairConfig(FlatAnalysisConfig):
    """Configuration for FlatPairTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='flat')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class FlatPairTask(FlatAnalysisTask):
    """Analyze some flat data"""

    ConfigClass = FlatPairConfig
    _DefaultName = "FlatPairTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        FlatAnalysisTask.__init__(self, **kwargs)
        self.stat_ctrl = afwMath.StatisticsControl()

    def mean(self, img):
        """Return the mean of an image"""
        return afwMath.makeStatistics(img, afwMath.MEAN, self.stat_ctrl).getValue()

    def var(self, img):
        """Return the variance of an image"""
        return afwMath.makeStatistics(img, afwMath.STDEVCLIP, self.stat_ctrl).getValue()**2

    def get_pair_stats(self, image_1, image_2):
        """Get the mean and varience from a pair of flats"""
        fratio_im = afwImage.ImageF(image_1, True)
        operator.itruediv(fratio_im, image_2)
        fratio = self.mean(fratio_im)
        image_2 *= fratio
        fmean = (self.mean(image_1) + self.mean(image_2))/2.

        fdiff = afwImage.ImageF(image_1, True)
        fdiff -= image_2
        fvar = self.var(fdiff)/2.
        return (fratio, fmean, fvar)

    def extract(self, butler, data, **kwargs):
        """Extract data

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
            Output data tables
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        flat1_files = data['FLAT1']
        flat2_files = data['FLAT2']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        gains = None

        sys.stdout.write("Working on %s, %i files: " % (slot, len(flat1_files)))
        sys.stdout.flush()

        # This is a dictionary of dictionaries to store all the
        # data you extract from the flat_files
        data_dict = dict(FLUX=[],
                         EXPTIME=[],
                         MONDIODE1=[], 
                         MONDIODE2=[])
        for i in range(1, 17):
            data_dict['AMP%02i_MEAN' % i] = []
            data_dict['AMP%02i_VAR' % i] = []
            data_dict['AMP%02i_SIGNAL' % i] = []

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        for i, (id_1, id_2) in enumerate(zip(flat1_files, flat2_files)):
            
            if i % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            flat_1 = get_ccd_from_id(butler, id_1, [])
            flat_2 = get_ccd_from_id(butler, id_2, [])

            amps = get_amp_list(butler, flat_1)

            flux_1 = get_exposure_time(butler, flat_1)
            flux_2 = get_exposure_time(butler, flat_2)

            if flux_1 != flux_2:
                raise RuntimeError("Exposure times do not match for:\n%s\n%s\n"
                                   % (id_1, id_1))
            data_dict['EXPTIME'].append(flux_1)

            mondiode_1 = get_mondiode_val(butler, flat_1)
            mondiode_2 = get_mondiode_val(butler, flat_2)

            if mondiode_1 is not None:
                flux_1 *= mondiode_1
                data_dict['MONDIODE1'].append(mondiode_1)
            else:
                data_dict['MONDIODE1'].append(-1)
            if mondiode_2 is not None:
                flux_2 *= mondiode_2
                data_dict['MONDIODE2'].append(mondiode_2)
            else:
                data_dict['MONDIODE2'].append(-1)
            flux = (flux_1 + flux_2)/2.

            data_dict['FLUX'].append(flux)

            for i, amp in enumerate(amps):
                regions = get_geom_regions(butler, flat_1, amp)
                serial_oscan = regions['serial_overscan']
                imaging = regions['imaging']
                #imaging.grow(-20)
                im_1 = get_raw_image(butler, flat_1, amp)
                im_2 = get_raw_image(butler, flat_2, amp)

                if superbias_frame is not None:
                    if butler is not None:
                        superbias_im = get_raw_image(None, superbias_frame, amp+1)
                    else:
                        superbias_im = get_raw_image(None, superbias_frame, amp)
                else:
                    superbias_im = None

                image_1 = unbias_amp(im_1, serial_oscan, bias_type=self.config.bias,
                                     superbias_im=superbias_im, region=imaging)
                image_2 = unbias_amp(im_2, serial_oscan, bias_type=self.config.bias,
                                     superbias_im=superbias_im, region=imaging)

                fstats = self.get_pair_stats(image_1, image_2)
                signal = fstats[1]
                if gains is not None:
                    signal *= gains[1]

                data_dict['AMP%02i_MEAN' % (i+1)].append(fstats[1])
                data_dict['AMP%02i_VAR' % (i+1)].append(fstats[2])
                data_dict['AMP%02i_SIGNAL' % (i+1)].append(signal)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, flat1_files + flat2_files))
        dtables.make_datatable('flat', data_dict)

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots 

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

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


EO_TASK_FACTORY.add_task_class('FlatPair', FlatPairTask)
