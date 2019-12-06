"""Class to analyze the FFT of the bias frames"""

import numpy as np

from scipy.interpolate import UnivariateSpline

from lsst.eo_utils.base import TableDict

from lsst.eo_utils.base.data_utils import create_dict_from_guard_rows, append_guard_row

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.factory import EO_TASK_FACTORY
from lsst.eo_utils.base.stat_utils import perform_linear_chisq_fit, make_profile_hist, LINEARITY_FUNC_DICT

from .meta_analysis import FlatSlotTableAnalysisConfig, FlatSlotTableAnalysisTask


def build_slitw_format_dict(slitw_vals):
    """Build a dict mapping the slit width vals to matplotlib format statements"""
    idx = 0
    odict = {}
    slit_fmt_list = ['r.', 'g.', 'b.', 'k.']
    n_slit_fmt = len(slit_fmt_list)
    for slitw in slitw_vals:
        if slitw not in odict:
            odict[slitw] = slit_fmt_list[idx % n_slit_fmt]
            idx += 1
    return odict


class NonlinearityConfig(FlatSlotTableAnalysisConfig):
    """Configuration for NonlinearityTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='flat-pair')
    filekey = EOUtilOptions.clone_param('filekey', default='flat-nonlin')
    nonlin_spline_ext = EOUtilOptions.clone_param('nonlin_spline_ext')
    nonlin_spline_smooth = EOUtilOptions.clone_param('nonlin_spline_smooth')


class NonlinearityTask(FlatSlotTableAnalysisTask):
    """Measue the linearity using data extracted from the flat-pair data"""

    ConfigClass = NonlinearityConfig
    _DefaultName = "NonlinearityTask"

    plot_resid_ymin = -0.02
    plot_resid_ymax = 0.02

    model_func_choice = 1
    do_profiles = True
    null_point = 0.
    num_profile_points = 40

    plot_names = ['fits', 'prof', 'nonlin',
                  'nonlin-log', 'nonlin-stack', 'nonlin-stack-log',
                  'fits-inv', 'prof-inv', 'nonlin-inv',
                  'nonlin-log-inv', 'nonlin-stack-inv', 'nonlin-stack-log-inv']

    @staticmethod
    def _correct_null_point(profile_x, profile_y, null_point):
        """Force the spline to go through zero at a particular x-xvalue

        Parameters
        ----------
        profile_x : `array`
            The x-bin centers
        profile_yerr : `array`
            The y-bin values
        null_point : `float`
            The x-value where the spline should go through zero

        Returns
        -------
        y_vals_offset
            The adjusted y-values
        """
        try:
            uni_spline = UnivariateSpline(profile_x, profile_y)
            offset = uni_spline(null_point)
        except Exception as msg:
            print("Failed to extract null point")
            print(msg)
            offset = 0.
        return ((1 + profile_y) / (1 + offset)) - 1.


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

        self.log_info_slot_msg(self.config, "")

        basename = data[0]
        datapath = basename.replace('flat.fits', '%s.fits' % self.config.infilekey)

        try:
            dtables = TableDict(datapath)
        except FileNotFoundError:
            return None

        try:
            tab = dtables['flat']
            exp_time = tab['EXPTIME']
            md_1 = tab['MONDIODE1']
            md_2 = tab['MONDIODE2']

            flux_1 = -1. * md_1 * exp_time
            flux_2 = -1. * md_2 * exp_time

            flux = (flux_1 + flux_2) / 2.
            slit_widths = tab['MONOCH_SLIT_B']
        except KeyError:
            tab = dtables['detector_response']
            flux = tab['flux']
            flux_1 = flux
            flux_2 = flux
            slit_widths = np.zeros(flux.shape)

        flux_vals = np.hstack([flux_1, flux_2])

        guard_vals_dict = dict(amp=0,
                               slope=0.,
                               curve=0.,
                               offset=0.,
                               frac_resid=np.zeros((len(flux_vals))),
                               frac_resid_err=np.zeros((len(flux_vals))))
        if self.do_profiles:
            if self.num_profile_points is not None:
                np_bins = self.num_profile_points - 1
            else:
                np_bins = len(flux_vals)
            guard_vals_dict['prof_x'] = np.zeros((np_bins))
            guard_vals_dict['prof_y'] = np.zeros((np_bins))
            guard_vals_dict['prof_y_corr'] = np.zeros((np_bins))
            guard_vals_dict['prof_yerr'] = np.zeros((np_bins))

        data_dict = create_dict_from_guard_rows(guard_vals_dict)
        data_dict_inv = create_dict_from_guard_rows(guard_vals_dict)

        copy_dict = dict(flux=flux,
                         flux_1=flux_1,
                         flux_2=flux_2,
                         monoch_slit_b=slit_widths)

        for amp in range(1, 17):

            # Here you can get the data out for each amp and append it to the
            # data_dict

            try:
                amp_val1 = tab['AMP%02i_MEAN1' % amp]
                amp_val2 = tab['AMP%02i_MEAN2' % amp]
            except KeyError:
                amp_val1 = tab['AMP%02i_SIGNAL' % amp]
                amp_val2 = tab['AMP%02i_SIGNAL' % amp]

            copy_dict['AMP%02i_MEAN1' % amp] = amp_val1
            copy_dict['AMP%02i_MEAN2' % amp] = amp_val2
            amp_vals = np.hstack([amp_val1, amp_val2])

            if amp_vals.size == 0:
                guard_vals_dict['amp'] = amp
                self.log.warn("No Amp values for amp %i, Writing guard values" % amp)
                append_guard_row(data_dict, guard_vals_dict)
                append_guard_row(data_dict_inv, guard_vals_dict)
                continue

            mask = amp_vals < 0.8 * amp_vals.max()
            #mask = amp_vals <= amp_vals.max()

            if not mask.any():
                guard_vals_dict['amp'] = amp
                self.log.warn("No frames passed cut for amp %i, Writing guard values" % amp)
                append_guard_row(data_dict, guard_vals_dict)
                append_guard_row(data_dict_inv, guard_vals_dict)
                continue

            data_dict['amp'].append(amp)
            data_dict_inv['amp'].append(amp)

            results, _, frac_resid, frac_resid_err =\
                perform_linear_chisq_fit(amp_vals, flux_vals, mask, self.model_func_choice)
            # Correct the error for the conversion to ne
            frac_resid_err *= results[0][0]

            results_inv, _, frac_resid_inv, frac_resid_err_inv =\
                perform_linear_chisq_fit(flux_vals, amp_vals, mask, self.model_func_choice)

            if self.do_profiles:
                if self.num_profile_points is not None:
                    profile_xbins = np.linspace(0., amp_vals[mask].max(), self.num_profile_points)
                    profile_xbins_inv = np.linspace(0., flux_vals[mask].max(), self.num_profile_points)

                    profile_x, profile_y, profile_yerr =\
                        make_profile_hist(profile_xbins, amp_vals, frac_resid,
                                          yerrs=frac_resid_err, stderr=True)
                    profile_x_inv, profile_y_inv, profile_yerr_inv =\
                       make_profile_hist(profile_xbins_inv, flux_vals, frac_resid_inv,
                                         yerrs=frac_resid_err_inv, stderr=True)
                else:
                    idx_sort = np.argsort(amp_vals)
                    idx_sort_inv = np.argsort(flux_vals)
                    profile_x, profile_y, profile_yerr =\
                        amp_vals[idx_sort], frac_resid[idx_sort], frac_resid_err[idx_sort]
                    profile_x_inv, profile_y_inv, profile_yerr_inv =\
                        flux_vals[idx_sort_inv], frac_resid_inv[idx_sort_inv],\
                        frac_resid_err_inv[idx_sort_inv]

                if self.null_point is not None:
                    profile_y_corr = self._correct_null_point(profile_x, profile_y, self.null_point)
                else:
                    profile_y_corr = profile_y

                data_dict['prof_x'].append(profile_x)
                data_dict['prof_y'].append(profile_y)
                data_dict['prof_y_corr'].append(profile_y_corr)
                data_dict['prof_yerr'].append(profile_yerr)

                data_dict_inv['prof_x'].append(profile_x_inv)
                data_dict_inv['prof_y'].append(profile_y_inv)
                data_dict_inv['prof_y_corr'].append(profile_y_inv)
                data_dict_inv['prof_yerr'].append(profile_yerr_inv)

            data_dict['slope'].append(results[0][0])
            data_dict_inv['slope'].append(results_inv[0][0])

            if self.model_func_choice > 1:
                data_dict['curve'].append(results[0][1])
                data_dict_inv['curve'].append(results_inv[0][1])
            else:
                data_dict['curve'].append(0.)
                data_dict_inv['curve'].append(0.)
            if self.model_func_choice > 2:
                data_dict['offset'].append(results[0][2])
                data_dict_inv['offset_inv'].append(results_inv[0][2])
            else:
                data_dict['offset'].append(0.)
                data_dict_inv['offset'].append(0.)

            data_dict['frac_resid'].append(frac_resid)
            data_dict['frac_resid_err'].append(frac_resid_err)

            data_dict_inv['frac_resid'].append(frac_resid_inv)
            data_dict_inv['frac_resid_err'].append(frac_resid_err_inv)

        self.log_progress("Done!")

        outtables = TableDict()
        outtables.make_datatable("nonlin", data_dict)
        outtables.make_datatable("nonlin-inv", data_dict_inv)
        outtables.make_datatable("flat_lin", copy_dict)
        return outtables


    def _plot_nonlinearity(self, flux, slit_widths, dtables, figs, **kwargs):
        """Plot the non-linearity data

        Parameters
        ----------
        flux : `array`
            The flux array
        slit_widths : `array`
            The monochoromter slit width values
        dtables : `TableDict`
            The table dictionary
        figs : `FigureDict`
            The resulting figures

        Keywords
        --------
        inverse : bool
            Flip the x and y axes
        """
        inverse = kwargs.get('inverse', False)

        if inverse:
            sfx = "-inv"
            xlabel_short = 'Flux [a.u.]'
            xlabel_full = "Photodiode Charge [nC]"
            ylabel = 'Mean [ADU]'
            ylabel_resid_short = 'Frac. Resid.'
            ylabel_resid_full = r'Frac. Resid. ($\frac{\mu - F(q)}{F(q)})$'
        else:
            sfx = ""
            xlabel_short = 'Mean [ADU]'
            xlabel_full = 'Mean [ADU]'
            ylabel = 'Flux [a.u.]'
            ylabel_resid_short = 'Frac. Resid.'
            ylabel_resid_full = r'Frac. Resid. ($\frac{q - F(\mu)}{F(\mu)})$'

        tab_nonlin = dtables['nonlin%s' % sfx]
        tab_flatlin = dtables['flat_lin']

        offsets = tab_nonlin['offset']
        slopes = tab_nonlin['slope']
        curves = tab_nonlin['curve']
        frac_resid_col = tab_nonlin['frac_resid']
        frac_resid_err_col = tab_nonlin['frac_resid_err']

        kw_spline = {}
        if self.config.nonlin_spline_ext is not None:
            kw_spline['ext'] = self.config.nonlin_spline_ext
        if self.config.nonlin_spline_smooth is not None:
            kw_spline['s'] = self.config.nonlin_spline_smooth

        model_func = LINEARITY_FUNC_DICT[self.model_func_choice]

        figs.setup_amp_resid_plots_grid('fits%s' % sfx, xlabel=xlabel_short,
                                        ylabel=ylabel, ylabel_resid=ylabel_resid_short,
                                        ymin_resid=-0.2, ymax_resid=0.2,
                                        xscale='log', yscale='log')
        figs.setup_amp_plots_grid('prof%s' % sfx, xlabel=xlabel_short,
                                  ylabel=ylabel_resid_full,
                                  ymin_resid=-0.2, ymax_resid=0.2,
                                  xscale='lin', yscale='log')

        fig_nonlin_log = figs.setup_figure("nonlin-log%s" % sfx,
                                           xlabel=xlabel_full, ylabel=ylabel_resid_full,
                                           figsize=(7, 5))
        axes_nonlin_log = fig_nonlin_log['axes']
        #axes_nonlin_log.set_xlim(1., 3000.)
        axes_nonlin_log.set_ylim(self.plot_resid_ymin, self.plot_resid_ymax)
        axes_nonlin_log.set_xscale('log')

        fig_nonlin = figs.setup_figure("nonlin%s" % sfx,
                                       xlabel=xlabel_full, ylabel=ylabel_resid_full,
                                       figsize=(7, 5))
        axes_nonlin = fig_nonlin['axes']
        #axes_nonlin.set_xlim(0., 3000.)
        axes_nonlin.set_ylim(self.plot_resid_ymin, self.plot_resid_ymax)

        fig_nonlin_log_stack = figs.setup_figure("nonlin-log-stack%s" % sfx,
                                                 xlabel=xlabel_full, ylabel=ylabel_resid_full,
                                                 figsize=(7, 5))
        axes_nonlin_log_stack = fig_nonlin_log_stack['axes']
        #axes_nonlin_log_stack.set_xlim(1., 3000.)
        axes_nonlin_log_stack.set_ylim(self.plot_resid_ymin, self.plot_resid_ymax)
        axes_nonlin_log_stack.set_xscale('log')

        fig_nonlin_stack = figs.setup_figure("nonlin-stack%s" % sfx,
                                             xlabel=xlabel_full, ylabel=ylabel_resid_full,
                                             figsize=(7, 5))
        axes_nonlin_stack = fig_nonlin_stack['axes']
        #axes_nonlin_stack.set_xlim(0., 3000.)
        axes_nonlin_stack.set_ylim(self.plot_resid_ymin, self.plot_resid_ymax)

        full_mask = np.ones(2*len(tab_flatlin), bool)

        for amp in range(1, 17):
            amp_vals_1 = tab_flatlin['AMP%02i_MEAN1' % amp]
            amp_vals_2 = tab_flatlin['AMP%02i_MEAN2' % amp]
            amp_vals = np.hstack([amp_vals_1, amp_vals_2])

            if amp_vals.size == 0:
                continue

            mask = amp_vals < 0.8 * amp_vals.max()
            #mask = amp_vals <= amp_vals.max()

            full_mask *= mask
            if not mask.any():
                continue

            iamp = amp - 1
            slope = slopes[iamp]
            curve = curves[iamp]
            offset = offsets[iamp]
            pars = (slope, curve, offset)

            if inverse:
                xvals = flux
                yvals = amp_vals
            else:
                xvals = amp_vals
                yvals = flux

            model_yvals = model_func(pars, xvals)
            xline = np.linspace(1., xvals[mask].max(), 1001)

            amp_plot_data = dict(xvals=xvals, yvals=yvals, resid_vals=frac_resid_col[iamp],
                                 model_vals=model_yvals, resid_errors=frac_resid_err_col[iamp],
                                 body_mask=None, resid_mask=mask)
            figs.plot_resid('fits%s' % sfx, amp-1, amp_plot_data)

            profile_x = tab_nonlin['prof_x'][amp-1]
            profile_y = tab_nonlin['prof_y'][amp-1]
            profile_y_corr = tab_nonlin['prof_y_corr'][amp-1]
            profile_yerr = tab_nonlin['prof_yerr'][amp-1]
            prof_mask = profile_yerr >= 0.

            axs_prof = figs['prof%s' % sfx]['axs'].flat[amp-1]
            axs_prof.errorbar(profile_x[prof_mask], profile_y[prof_mask],
                              yerr=profile_yerr[prof_mask], fmt='.')
            axs_prof.errorbar(profile_x[prof_mask], profile_y_corr[prof_mask],
                              yerr=profile_yerr[prof_mask], fmt='+')

            x_masked = xvals[mask]
            y_resid_masked = frac_resid_col[iamp][mask]
            idx_sort = np.argsort(x_masked)
            if amp <= 8:
                fmt = '-'
            else:
                fmt = '-'

            try:
                uni_spline = UnivariateSpline(profile_x[prof_mask], profile_y[prof_mask], **kw_spline)
                axs_prof.plot(xline, uni_spline(xline), 'r-')
                uni_spline_corr = UnivariateSpline(profile_x[prof_mask],
                                                   profile_y_corr[prof_mask],
                                                   **kw_spline)
                axs_prof.plot(xline, uni_spline_corr(xline), 'g-')
            except Exception:
                pass

            axes_nonlin.plot(x_masked[idx_sort], y_resid_masked[idx_sort], fmt, label="Amp %i" % amp)
            axes_nonlin_log.plot(x_masked[idx_sort], y_resid_masked[idx_sort], fmt, label="Amp %i" % amp)

        stack_means_a0 = frac_resid_col[0:8,].mean(0)
        stack_stds_a0 = frac_resid_col[0:8,].std(0)
        stack_means_a1 = frac_resid_col[8:,].mean(0)
        stack_stds_a1 = frac_resid_col[8:,].std(0)

        slit_formats = build_slitw_format_dict(slit_widths)

        for slit_key, slit_format in slit_formats.items():
            m_mask = np.fabs(slit_widths - slit_key) < 1
            m_mask *= full_mask
            axes_nonlin_log_stack.errorbar(xvals[m_mask], stack_means_a0[m_mask], yerr=stack_stds_a0[m_mask],
                                           fmt=slit_format, label="%.0f ASPIC 0" % slit_key)
            axes_nonlin_log_stack.errorbar(xvals[m_mask], stack_means_a1[m_mask], yerr=stack_stds_a1[m_mask],
                                           fmt=slit_format.replace('.', '+'), label="%.0f ASPIC 1" % slit_key)
            axes_nonlin_stack.errorbar(xvals[m_mask], stack_means_a0[m_mask], yerr=stack_stds_a0[m_mask],
                                       fmt=slit_format, label="%.0f ASPIC 0" % slit_key)
            axes_nonlin_stack.errorbar(xvals[m_mask], stack_means_a1[m_mask], yerr=stack_stds_a1[m_mask],
                                       fmt=slit_format.replace('.', '+'), label="%.0f ASPIC 1" % slit_key)
        axes_nonlin_log_stack.legend()
        axes_nonlin_stack.legend()


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data

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

        tab_flatlin = dtables['flat_lin']

        flux_1 = tab_flatlin['flux_1']
        flux_2 = tab_flatlin['flux_2']
        flux = np.hstack([flux_1, flux_2])

        slit_widths = tab_flatlin['monoch_slit_b']
        slit_widths = np.hstack([slit_widths, slit_widths])

        self._plot_nonlinearity(flux, slit_widths, dtables, figs)
        self._plot_nonlinearity(flux, slit_widths, dtables, figs, inverse=True)


EO_TASK_FACTORY.add_task_class('Nonlinearity', NonlinearityTask)
