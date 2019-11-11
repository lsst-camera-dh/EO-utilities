"""Class to analyze the photon transfer curve"""

import scipy.optimize

import numpy as np

from lsst.eotest.sensor.ptcTask import ptc_func

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .meta_analysis import  FlatRaftTableAnalysisConfig,\
    FlatRaftTableAnalysisTask,\
    FlatSummaryAnalysisConfig, FlatSummaryAnalysisTask


def model_func_quad(pars, xvals):
    """Return a quadratic function of xvals"""
    #return pars[0] + pars[1]*xvals + pars[2]*xvals*xvals
    #return pars[0]*xvals + pars[1]*xvals*xvals
    return pars[0] + pars[1]*xvals + pars[2]*xvals*xvals


def chi2_model(pars, xvals, yvals, model):
    """Return the chi2 w.r.t. the model"""
    return (yvals - model(pars, xvals))/np.sqrt(yvals)



class PTCConfig(FlatRaftTableAnalysisConfig):
    """Configuration for PTCStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='flat')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='ptc')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class PTCTask(FlatRaftTableAnalysisTask):
    """Extract statistics about the photon transfer curves"""

    ConfigClass = PTCConfig
    _DefaultName = "PTCTask"

    def extract(self, butler, data, **kwargs):
        """Extract the PTC summary statistics

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

        if butler is not None:
            self.log.warn("Ignoring butler")

        data_dict = dict(npts=[],
                         nused=[],
                         ptc_mean=[],
                         ptc_var=[],
                         med_gain=[],
                         a00=[],
                         a00_error=[],
                         alpha=[],
                         alpha_error=[],
                         gain=[],
                         gain_error=[],
                         slot=[],
                         amp=[])

        self.log_info_raft_msg(self.config, "")

        slots = self.config.slots
        if slots is None:
            slots = ALL_SLOTS

        for islot, slot in enumerate(slots):

            self.log_progress("  %s" % slot)

            dtables = TableDict(data[slot].replace('flat.fits', '%s.fits' % self.config.insuffix))

            try:
                tab = dtables['flat']
            except KeyError:
                tab = dtables['ptc_stats']

            for amp in range(1, 17):
                mean = tab["AMP%02i_CORRMEAN" % (amp)]
                var = tab["AMP%02i_VAR" % (amp)]
                med_gain = np.median(mean/var)
                frac_resids = np.abs((var - mean/med_gain)/var)
                index = np.where(frac_resids < 0.2)
                #index = var < 0.4 * var.max()
                try:
                    pars = (2.7e-6, med_gain, 25.)
                    #pars = (25., med_gain, 0.)
                    results = scipy.optimize.leastsq(chi2_model, pars, full_output=1,
                                                     args=(mean[index], var[index], ptc_func))
                    pars, cov = results[:2]
                    ptc_a00 = pars[0]
                    ptc_gain = pars[1]
                    ptc_alpha = pars[2]
                    if cov is not None:
                        ptc_a00_error = np.sqrt(cov[0][0])
                        ptc_gain_error = np.sqrt(cov[1][1])
                        ptc_alpha_error = np.sqrt(cov[2][2])
                    else:
                        ptc_a00_error = -1.
                        ptc_alpha_error = -1.
                        ptc_gain_error = -1.
                except Exception as eobj:
                    self.log.warn("Exception caught while fitting PTC:")
                    self.log.warn(str(eobj))
                    ptc_a00 = 0.
                    ptc_a00_error = -1.
                    ptc_gain = 0.
                    ptc_gain_error = -1.
                    ptc_alpha = 0.
                    ptc_alpha_error = -1.
                data_dict['ptc_mean'].append(mean)
                data_dict['ptc_var'].append(var)
                data_dict['npts'].append(mean.size)
                data_dict['nused'].append(len(index))
                data_dict['med_gain'].append(med_gain)
                data_dict['a00'].append(ptc_a00)
                data_dict['a00_error'].append(ptc_a00_error)
                data_dict['alpha'].append(ptc_alpha)
                data_dict['alpha_error'].append(ptc_alpha_error)
                data_dict['gain'].append(ptc_gain)
                data_dict['gain_error'].append(ptc_gain_error)
                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp-1)

        self.log_progress("Done!")

        outtables = TableDict()
        outtables.make_datatable("ptc", data_dict)
        return outtables


    @staticmethod
    def plot_fits(dtables, figs):
        """Plot the amplifier by amplifier fits from the ptc study

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        """
        table = dtables['ptc']
        ptc_means = table['ptc_mean']
        ptc_vars = table['ptc_var']
        a00s = table['a00']
        alphas = table['alpha']
        gains = table['gain']

        idx = 0
        for slot in ALL_SLOTS:

            _ = figs.setup_amp_resid_plots_grid('ptc_fits_%s' % slot, xlabel='Mean [ADU]',
                                                ylabel='VARIANCE [ADU**2]',
                                                ylabel_resid='Frac. Resid.',
                                                xmin=10., xmax=250000.,
                                                ymin=10., ymax=250000,
                                                ymin_resid=-0.2, ymax_resid=0.2,
                                                xscale='log', yscale='log')

            fig_nonlin_log = figs.setup_figure("non_lin_log_%s" % slot,
                                               xlabel="Flux [a.u.]",
                                               ylabel='Frac. Resid',
                                               figsize=(7, 5))
            axes_nonlin_log = fig_nonlin_log['axes']
            axes_nonlin_log.set_xscale('log')

            fig_nonlin = figs.setup_figure("non_lin_%s" % slot, xlabel="Flux [a.u.]", ylabel='Frac. Resid',
                                           figsize=(7, 5))
            axes_nonlin = fig_nonlin['axes']

            for amp in range(16):
                try:
                    xvals = ptc_means[idx]
                except IndexError:
                    break

                sort_idx = np.argsort(xvals)
                xvals = xvals[sort_idx]
                yvals = ptc_vars[idx][sort_idx]

                ptc_pars = (a00s[idx], gains[idx], alphas[idx])
                yvals_fit = ptc_func(ptc_pars, xvals)
                frac_resid = (yvals - yvals_fit)/yvals_fit
                mask = np.fabs(frac_resid) < 0.2
                x_masked = xvals[mask]
                y_masked = frac_resid[mask]

                amp_plot_data = dict(xvals=xvals, yvals=yvals, resid_vals=frac_resid,
                                     model_vals=yvals_fit, body_mask=mask, resid_mask=mask)
                figs.plot_resid('ptc_fits_%s' % slot, amp, amp_plot_data)

                axes_nonlin.plot(x_masked, y_masked, '-', label="Amp %i" % amp)
                axes_nonlin_log.plot(x_masked, y_masked, '-', label="Amp %i" % amp)

                idx += 1




    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the ptc statistics study

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
        self.plot_fits(dtables, figs)

        #sumtable = dtables['ptc_stats']
        #figs.plot_stat_color('gain_array', sumtable['gain'].reshape(9,16))


class PTCSummaryConfig(FlatSummaryAnalysisConfig):
    """Configuration for PTCSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='ptc')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='ptc_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class PTCSummaryTask(FlatSummaryAnalysisTask):
    """Summarize the results for the analysis of variations of the
    photon transfer curves frames"""

    ConfigClass = PTCSummaryConfig
    _DefaultName = "PTCSummaryTask"

    def extract(self, butler, data, **kwargs):
        """Extract the summary data from the PTC analyses

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

        if butler is not None:
            self.log.warn("Ignoring butler")

        for key, val in data.items():
            data[key] = val.replace('_ptc_sum.fits', '_ptc_stats.fits')

        remove_cols = ['ptc_mean', 'ptc_var']

        if not self.config.skip:
            outtable = vstack_tables(data, tablename='ptc',
                                     remove_cols=remove_cols)

        dtables = TableDict()
        dtables.add_datatable('ptc_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the PTC analyses

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
        sumtable = dtables['ptc_sum']
        runtable = dtables['runs']

        yvals = sumtable['gain'].flatten().clip(0., 2.)
        yerrs = sumtable['gain_error'].flatten().clip(0., 0.5)
        runs = runtable['runs']

        figs.plot_run_chart("ptc_gain", runs, yvals, yerrs=yerrs, ylabel="Gain")


EO_TASK_FACTORY.add_task_class('PTC', PTCTask)
EO_TASK_FACTORY.add_task_class('PTCSummary', PTCSummaryTask)
