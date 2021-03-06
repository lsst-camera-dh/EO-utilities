"""Class to construct superbias frames"""

import numpy as np

from astropy.io import fits

import lsst.afw.math as afwMath

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_amp_list,\
    get_exposure_time, unbiased_ccd_image_dict,\
    get_monodiode_val_from_data_id

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .analysis import SflatAnalysisConfig,\
    SflatAnalysisTask


class StabilityConfig(SflatAnalysisConfig):
    """Configuration for StabilityTask"""
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    filekey = EOUtilOptions.clone_param('filekey', default='sflat-stab')


class StabilityTask(SflatAnalysisTask):
    """Construct superflat frames"""

    ConfigClass = StabilityConfig
    _DefaultName = "StabilityTask"
    iteratorClass = AnalysisBySlot

    plot_names = ['delta-hist', 'delta', 'mean-ref', 'mean', 'std', 'row', 'col']

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

    def get_stats(self, image):
        """Get the mean and varience from a pair of flats"""
        fmean = self.mean(image)
        fmedian = self.median(image)
        fvar = self.var(image)
        return (fmean, fmedian, fvar)

    def extract(self, butler, data, **kwargs):
        """Compare frames to superflat

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

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)
        bias_type = self.get_bias_algo()

        sflat_files = data['SFLAT']

        if not sflat_files:
            self.log_warn_slot_msg(self.config, "No superflat files")
            return None

        self.log_info_slot_msg(self.config, "%i files" % (len(sflat_files)))

        # This is a dictionary of dictionaries to store all the
        # data you extract from the flat_files
        data_dict = dict(FLUX=[],
                         EXPTIME=[],
                         MONDIODE=[])

        for i in range(1, 17):
            data_dict['AMP%02i_FLAT_MEAN' % i] = []
            data_dict['AMP%02i_FLAT_MEDIAN' % i] = []
            data_dict['AMP%02i_FLAT_VAR' % i] = []
            data_dict['AMP%02i_FLAT_ROWMEAN' % i] = []
            data_dict['AMP%02i_FLAT_COLMEAN' % i] = []

        for ifile, sflat_file in enumerate(sflat_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            sflat = self.get_ccd(butler, sflat_file, mask_files)

            exp_time = get_exposure_time(sflat)
            mondiode = get_monodiode_val_from_data_id(sflat_file, exp_time,
                                                      self.config.teststand, butler)
            if mondiode is None:
                continue

            flux = exp_time * mondiode
            data_dict['EXPTIME'].append(exp_time)
            data_dict['MONDIODE'].append(mondiode)
            data_dict['FLUX'].append(flux)

            ccd_ims = unbiased_ccd_image_dict(sflat, bias=bias_type,
                                              superbias_frame=superbias_frame,
                                              trim='imaging')


            amps = get_amp_list(sflat)
            for amp in amps:
                image = ccd_ims[amp]
                fstats = self.get_stats(image)

                data_dict['AMP%02i_FLAT_MEAN' % amp].append(fstats[0])
                data_dict['AMP%02i_FLAT_MEDIAN' % amp].append(fstats[1])
                data_dict['AMP%02i_FLAT_VAR' % amp].append(fstats[2])
                data_dict['AMP%02i_FLAT_ROWMEAN' % amp].append(image.image.array.mean(0))
                data_dict['AMP%02i_FLAT_COLMEAN' % amp].append(image.image.array.mean(1))

        self.log_progress("Done!")

        primary_hdu = fits.PrimaryHDU()
        primary_hdu.header['NAMPS'] = 16

        dtables = TableDict(primary=primary_hdu)
        dtables.make_datatable('files', make_file_dict(butler, sflat_files))
        dtables.make_datatable('stability', data_dict)

        return dtables


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

        label_seq = 'Seq. Num.'
        label_delta = "Delta [ADU]"
        label_resid = 'Frac. Resid'
        label_std = 'Std. [ADU]'


        tab_stab = dtables['stability']
        figs.setup_amp_plots_grid('delta', xlabel=label_seq, ylabel=label_delta,
                                  ymin=-10, ymax=10)
        figs.setup_amp_plots_grid('delta-hist', xlabel=label_delta, ylabel="Frames/0.1ADU")
        figs.setup_amp_plots_grid('mean-ref', xlabel=label_seq, ylabel=label_resid,
                                  ymin=-0.001, ymax=0.001)
        figs.setup_amp_plots_grid('mean', xlabel=label_seq, ylabel=label_resid,
                                  ymin=-0.01, ymax=0.01)
        figs.setup_amp_plots_grid('std', xlabel=label_seq, ylabel=label_std)
        figs.setup_amp_plots_grid('row', xlabel="row", ylabel=label_seq)
        figs.setup_amp_plots_grid('col', xlabel="col", ylabel=label_seq)
        figs.setup_amp_plots_grid('delta-v-std', xlabel=label_delta, ylabel=label_std)

        flux = -1. * tab_stab['FLUX']

        refs = np.mean(np.vstack([tab_stab['AMP%02i_FLAT_MEAN' % amp] for amp in range(1, 17)]), 0)

        for amp in range(1, 17):
            amp_means = tab_stab['AMP%02i_FLAT_MEAN' % amp] / flux
            amp_vars = tab_stab['AMP%02i_FLAT_VAR' % amp] / (tab_stab['AMP%02i_FLAT_MEAN' % amp] * flux)
            ymedian = np.median(amp_means)
            ymedian_std = np.sqrt(np.median(amp_vars))
            std_delta = np.sqrt(amp_vars) - ymedian_std
            n_x = len(amp_means)
            xvals = np.linspace(0, n_x-1, n_x)
            frac_resid = (amp_means - ymedian) / ymedian

            norm_delta = tab_stab['AMP%02i_FLAT_MEAN' % amp] - refs
            norm_delta -= np.median(norm_delta)

            norm_frac_resid = (tab_stab['AMP%02i_FLAT_MEAN' % amp] - refs) / refs
            norm_frac_resid -= np.median(norm_frac_resid)
            figs.plot_hist('delta-hist', amp-1, norm_delta[20:-20], xmin=-10, xmax=10., nbins=100)
            figs.plot('delta', amp-1, xvals, norm_delta)
            figs.plot('mean-ref', amp-1, xvals, norm_frac_resid)
            figs.plot('mean', amp-1, xvals, frac_resid)
            figs.plot('std', amp-1, xvals, std_delta)

            rows = ((tab_stab['AMP%02i_FLAT_ROWMEAN'  % amp].T - refs) / flux).T
            cols = ((tab_stab['AMP%02i_FLAT_COLMEAN'  % amp].T - refs) / flux).T

            axes_scat = figs.get_amp_axes('delta-v-std', amp-1)
            axes_scat.set_xlim(-5., 5.)
            axes_scat.set_ylim(-0.005, 0.005)

            axes_scat.scatter(norm_delta, std_delta)

            #nrow = len(rows[0])
            #xrow = np.linspace(0, nrow-1, nrow)
            #ncol = len(cols[0])
            #xcol = np.linspace(0, ncol-1, ncol)

            med_row = np.median(rows, axis=0)
            med_col = np.median(cols, axis=0)

            figs.plot_2d_color("row", amp-1, rows-med_row,
                               origin='low', interpolation='none')
            figs.plot_2d_color("col", amp-1, cols-med_col,
                               origin='low', interpolation='none')

EO_TASK_FACTORY.add_task_class('Stability', StabilityTask)
