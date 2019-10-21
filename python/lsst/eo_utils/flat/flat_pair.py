"""Analyze the flat pairs data"""

import operator

import numpy as np

from astropy.io import fits

from scipy.integrate import trapz, simps

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_amp_list,\
    get_exposure_time, get_mondiode_val, get_mono_slit_b, unbiased_ccd_image_dict


from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig, FlatAnalysisTask


def get_mondiode_data(fits_file, factor=5):
    """Get the monitoring diode data"""
    with fits.open(fits_file) as hdus:
        hdu = hdus['AMP0.MEAS_TIMES']
        xvals = hdu.data.field('AMP0_MEAS_TIMES')
        yvals = -1.0e9*hdu.data.field('AMP0_A_CURRENT')
    ythresh = (max(yvals) - min(yvals))/factor + min(yvals)
    index = np.where(yvals < ythresh)
    y_0 = np.median(yvals[index])
    yvals -= y_0
    return xvals, yvals

def avg_sum(times, currents):
    """Computing the photodiode charge as the product of the
    bin widths and the bin values.
    This is b/c the picoampmeter return the averaged time
    for each interval"""
    del_t = times[1:] - times[0:-1]
    return (currents[1:] * del_t).sum()


class FlatPairConfig(FlatAnalysisConfig):
    """Configuration for FlatPairTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='flat')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    gain = EOUtilOptions.clone_param('gain')
    mask = EOUtilOptions.clone_param('mask')
    nonlin = EOUtilOptions.clone_param('nonlin')


class FlatPairTask(FlatAnalysisTask):
    """Analyze some flat pair data to extract means and variances"""

    ConfigClass = FlatPairConfig
    _DefaultName = "FlatPairTask"
    iteratorClass = AnalysisBySlot

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

        flat1_files = data['FLAT1']
        flat2_files = data['FLAT2']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        nlc = self.get_nonlinearirty_correction()
        gains = self.get_gains()
        slot_idx = ALL_SLOTS.index(self.config.slot)

        self.log_info_slot_msg(self.config, "%i files" % len(flat1_files))

        # This is a dictionary of dictionaries to store all the
        # data you extract from the flat_files
        data_dict = dict(FLUX=[],
                         FLUX_trapz=[],
                         FLUX_simps=[],
                         FLUX_avg=[],
                         FLUX_mondiode=[],
                         EXPTIME=[],
                         MONDIODE1=[],
                         MONDIODE1_trapz=[],
                         MONDIODE1_simps=[],
                         MONDIODE1_avg=[],
                         MONDIODE2=[],
                         MONDIODE2_trapz=[],
                         MONDIODE2_simps=[],
                         MONDIODE2_avg=[],
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

            flat_1 = get_ccd_from_id(butler, id_1, mask_files)
            flat_2 = get_ccd_from_id(butler, id_2, mask_files)

            amps = get_amp_list(flat_1)

            exp_time_1 = get_exposure_time(flat_1)
            exp_time_2 = get_exposure_time(flat_2)

            if exp_time_1 != exp_time_2:
                raise RuntimeError("Exposure times do not match for:\n%s\n%s\n"
                                   % (id_1, id_1))
            data_dict['EXPTIME'].append(exp_time_1)

            mon_diode_1_x, mon_diode_1_y = get_mondiode_data(id_1)
            mon_diode_2_x, mon_diode_2_y = get_mondiode_data(id_2)

            mon_diode_trapz_1 = trapz(mon_diode_1_y, mon_diode_1_x) / exp_time_1
            mon_diode_trapz_2 = trapz(mon_diode_2_y, mon_diode_2_x) / exp_time_2

            mon_diode_simps_1 = simps(mon_diode_1_y, mon_diode_1_x) / exp_time_1
            mon_diode_simps_2 = simps(mon_diode_2_y, mon_diode_2_x) / exp_time_2

            mon_diode_avg_1 = avg_sum(mon_diode_1_y, mon_diode_1_x) / exp_time_1
            mon_diode_avg_2 = avg_sum(mon_diode_2_y, mon_diode_2_x) / exp_time_2

            flux_trapz = exp_time_1 * (mon_diode_trapz_1 + mon_diode_trapz_2)/2.
            flux_simps = exp_time_1 * (mon_diode_simps_1 + mon_diode_simps_2)/2.
            flux_avg = -1. * exp_time_1 * (mon_diode_avg_1 + mon_diode_avg_2)/2.

            data_dict['MONDIODE1_trapz'].append(mon_diode_trapz_1)
            data_dict['MONDIODE1_simps'].append(mon_diode_simps_1)
            data_dict['MONDIODE1_avg'].append(mon_diode_avg_1)
            data_dict['MONDIODE2_trapz'].append(mon_diode_trapz_2)
            data_dict['MONDIODE2_simps'].append(mon_diode_simps_2)
            data_dict['MONDIODE2_avg'].append(mon_diode_avg_2)

            data_dict['FLUX_trapz'].append(flux_trapz)
            data_dict['FLUX_simps'].append(flux_simps)
            data_dict['FLUX_avg'].append(flux_avg)

            mondiode_1 = get_mondiode_val(flat_1)
            mondiode_2 = get_mondiode_val(flat_2)

            if mondiode_1 is not None:
                flux_1 = exp_time_1 * mondiode_1
                data_dict['MONDIODE1'].append(mondiode_1)
            else:
                data_dict['MONDIODE1'].append(-1)
            if mondiode_2 is not None:
                flux_2 = exp_time_2 * mondiode_2
                data_dict['MONDIODE2'].append(mondiode_2)
            else:
                data_dict['MONDIODE2'].append(-1)

            flux = (flux_1 + flux_2)/2.
            data_dict['FLUX'].append(flux_avg)
            data_dict['FLUX_mondiode'].append(flux)
            data_dict['MONOCH_SLIT_B'].append(get_mono_slit_b(flat_1))

            ccd_1_ims = unbiased_ccd_image_dict(flat_1, bias=self.config.bias,
                                                superbias_frame=superbias_frame,
                                                trim='imaging', nonlinearity=nlc)
            ccd_2_ims = unbiased_ccd_image_dict(flat_2, bias=self.config.bias,
                                                superbias_frame=superbias_frame,
                                                trim='imaging', nonlinearity=nlc)


            for i, amp in enumerate(amps):
                image_1 = ccd_1_ims[amp]
                image_2 = ccd_2_ims[amp]

                fstats = self.get_pair_stats(image_1, image_2)
                signal = fstats[1]
                if gains is not None:
                    signal *= gains[slot_idx][i]

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
