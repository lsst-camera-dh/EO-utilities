"""Analyze the flat pairs data"""

import operator

from astropy.io import fits

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_amp_list,\
    get_exposure_time, get_mono_slit_b, unbiased_ccd_image_dict,\
    get_monodiode_val_from_data_id

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig, FlatAnalysisTask




class FlatPairConfig(FlatAnalysisConfig):
    """Configuration for FlatPairTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='flat-pair')
    nonlin_spline_ext = EOUtilOptions.clone_param('nonlin_spline_ext')
    nonlin_spline_smooth = EOUtilOptions.clone_param('nonlin_spline_smooth')


class FlatPairTask(FlatAnalysisTask):
    """Analyze some flat pair data to extract means and variances"""

    ConfigClass = FlatPairConfig
    _DefaultName = "FlatPairTask"
    iteratorClass = AnalysisBySlot

    plot_names = []

    def mean(self, img):
        """Return the mean of an image"""
        return afwMath.makeStatistics(img, afwMath.MEAN, self.stat_ctrl).getValue()

    def median(self, img):
        """Return the mean of an image"""
        return afwMath.makeStatistics(img, afwMath.MEDIAN, self.stat_ctrl).getValue()

    def var(self, img):
        """Return the variance of an image"""
        #return afwMath.makeStatistics(img, afwMath.VARIANCECLIP, self.stat_ctrl).getValue()
        return afwMath.makeStatistics(img, afwMath.VARIANCE, self.stat_ctrl).getValue()

    def get_pair_stats(self, image_1, image_2):
        """Get the mean and varience from a pair of flats"""
        fmean1 = self.mean(image_1)
        fmean2 = self.mean(image_2)

        fratio_im = afwImage.MaskedImageF(image_1, True)
        fcopy_im = afwImage.MaskedImageF(image_2, True)

        operator.itruediv(fratio_im, image_2)
        fratio = self.mean(fratio_im)
        fcopy_im *= fratio
        fmean = (fmean1 + fmean2)/2.
        fcorrmean = (fmean1 + self.mean(fcopy_im))/2.

        fdiff = afwImage.MaskedImageF(image_1, True)
        fdiff -= fcopy_im
        fvar = self.var(fdiff)/2.
        return (fratio, fmean, fcorrmean, fvar, fmean1, fmean2)


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

        if self.config.teststand == 'ts8':
            flat1_files = data['FLAT1']
            flat2_files = data['FLAT2']
        elif self.config.teststand == 'bot':
            flat1_files = data['FLAT0']
            flat2_files = data['FLAT1']

        bias_type = self.get_bias_algo()
        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        nlc = self.get_nonlinearirty_correction()
        #gains = self.get_gains()
        #slot_idx = ALL_SLOTS.index(self.config.slot)

        if nlc is not None:
            print("using linearity corrections")

        self.log_info_slot_msg(self.config, "%i %i files" % (len(flat1_files), len(flat2_files)))

        # This is a dictionary of dictionaries to store all the
        # data you extract from the flat_files
        data_dict = dict(FLUX=[],
                         EXPTIME=[],
                         MONDIODE1=[],
                         MONDIODE2=[],
                         MONOCH_SLIT_B=[])

        for i in range(1, 17):
            data_dict['AMP%02i_RATIO' % i] = []
            data_dict['AMP%02i_MEAN' % i] = []
            data_dict['AMP%02i_CORRMEAN' % i] = []
            data_dict['AMP%02i_VAR' % i] = []
            data_dict['AMP%02i_SIGNAL' % i] = []
            data_dict['AMP%02i_MEAN1' % i] = []
            data_dict['AMP%02i_MEAN2' % i] = []


        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        for ifile, (id_1, id_2) in enumerate(zip(flat1_files, flat2_files)):

            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            flat_1 = self.get_ccd(butler, id_1, mask_files)
            flat_2 = self.get_ccd(butler, id_2, mask_files)

            amps = get_amp_list(flat_1)

            exp_time_1 = get_exposure_time(flat_1)
            exp_time_2 = get_exposure_time(flat_2)

            if exp_time_1 != exp_time_2:
                self.log.warn("Exposure times do not match for:\n%s\n%s\n   %0.3F %0.3F. Skipping Pair\n"
                              % (id_1, id_2, exp_time_1, exp_time_2))
                continue

            mondiode_1 = get_monodiode_val_from_data_id(id_1, exp_time_1,
                                                        self.config.teststand, butler)
            mondiode_2 = get_monodiode_val_from_data_id(id_2, exp_time_2,
                                                        self.config.teststand, butler)

            if mondiode_1 is None or mondiode_2 is None:
                self.log.warn("No monitoring data for:\n%s\n%s\n Skipping Pair\n"
                              % (id_1, id_2))
                continue

            flux = (exp_time_1 * mondiode_1 + exp_time_2 * mondiode_2)/2.

            data_dict['EXPTIME'].append(exp_time_1)
            data_dict['MONDIODE1'].append(mondiode_1)
            data_dict['MONDIODE2'].append(mondiode_2)
            data_dict['FLUX'].append(flux)

            try:
                data_dict['MONOCH_SLIT_B'].append(get_mono_slit_b(flat_1))
            except KeyError:
                data_dict['MONOCH_SLIT_B'].append(0.)

            ccd_1_ims = unbiased_ccd_image_dict(flat_1, bias=bias_type,
                                                superbias_frame=superbias_frame,
                                                trim='imaging', nonlinearity=nlc)
            ccd_2_ims = unbiased_ccd_image_dict(flat_2, bias=bias_type,
                                                superbias_frame=superbias_frame,
                                                trim='imaging', nonlinearity=nlc)

            for i, amp in enumerate(amps):
                image_1 = ccd_1_ims[amp]
                image_2 = ccd_2_ims[amp]

                fstats = self.get_pair_stats(image_1, image_2)
                signal = fstats[1]
                #if gains is not None:
                #    signal *= gains[slot_idx][i]

                data_dict['AMP%02i_RATIO' % (i+1)].append(fstats[0])
                data_dict['AMP%02i_MEAN' % (i+1)].append(fstats[1])
                data_dict['AMP%02i_CORRMEAN' % (i+1)].append(fstats[2])
                data_dict['AMP%02i_VAR' % (i+1)].append(fstats[3])
                data_dict['AMP%02i_SIGNAL' % (i+1)].append(signal)
                data_dict['AMP%02i_MEAN1' % (i+1)].append(fstats[4])
                data_dict['AMP%02i_MEAN2' % (i+1)].append(fstats[5])

        self.log_progress("Done!")

        primary_hdu = fits.PrimaryHDU()
        primary_hdu.header['NAMPS'] = 16

        dtables = TableDict(primary=primary_hdu)
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
