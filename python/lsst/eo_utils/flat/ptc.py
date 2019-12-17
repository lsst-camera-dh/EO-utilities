"""Class to analyze the photon transfer curve"""

import os

import scipy.optimize

import numpy as np

from lsst.eotest.sensor.ptcTask import ptc_func

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .meta_analysis import FlatSlotTableAnalysisConfig,\
    FlatSlotTableAnalysisTask,\
    FlatRaftTableAnalysisConfig, FlatRaftTableAnalysisTask,\
    FlatSummaryAnalysisConfig, FlatSummaryAnalysisTask


def model_func_quad(pars, xvals):
    """Return a quadratic function of xvals"""
    #return pars[0] + pars[1]*xvals + pars[2]*xvals*xvals
    #return pars[0]*xvals + pars[1]*xvals*xvals
    return pars[0] + pars[1]*xvals + pars[2]*xvals*xvals


def chi2_model(pars, xvals, yvals, model):
    """Return the chi2 w.r.t. the model"""
    return (yvals - model(pars, xvals))/np.sqrt(yvals)



class PTCConfig(FlatSlotTableAnalysisConfig):
    """Configuration for PTCStatsTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='flat-pair')
    filekey = EOUtilOptions.clone_param('filekey', default='ptc')


class PTCTask(FlatSlotTableAnalysisTask):
    """Extract statistics about the photon transfer curves"""

    ConfigClass = PTCConfig
    _DefaultName = "PTCTask"

    plot_names = ['fits', 'nonlin-log', 'nonlin']

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
                         amp=[])

        self.log_info_raft_msg(self.config, "")

        try:
            dtables = TableDict(data[0])
        except FileNotFoundError:
            print("Skipping ", data[0])
            return None

        try:
            tab = dtables['flat']
            mean_sfx = "CORRMEAN"
        except KeyError:
            tab = dtables['ptc_stats']
            mean_sfx = "MEAN"

        for amp in range(1, 17):
            mean = tab["AMP%02i_%s" % (amp, mean_sfx)]
            var = tab["AMP%02i_VAR" % (amp)]
            med_gain = np.median(mean/var)
            try:
                #index = np.where(frac_resids < 0.2)
                index = mean < 8.0e4
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
                nused = len(index)
            except Exception as eobj:
                self.log.warn("Exception caught while fitting PTC:")
                self.log.warn(str(eobj))

                ptc_a00 = 0.
                ptc_a00_error = -1.
                ptc_gain = 0.
                ptc_gain_error = -1.
                ptc_alpha = 0.
                ptc_alpha_error = -1.
                nused = 0
            data_dict['ptc_mean'].append(mean)
            data_dict['ptc_var'].append(var)
            data_dict['npts'].append(mean.size)
            data_dict['nused'].append(nused)
            data_dict['med_gain'].append(med_gain)
            data_dict['a00'].append(ptc_a00)
            data_dict['a00_error'].append(ptc_a00_error)
            data_dict['alpha'].append(ptc_alpha)
            data_dict['alpha_error'].append(ptc_alpha_error)
            data_dict['gain'].append(ptc_gain)
            data_dict['gain_error'].append(ptc_gain_error)
            data_dict['amp'].append(amp-1)

        self.log_progress("Done!")

        if nused == 0:
            return None

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

        _ = figs.setup_amp_resid_plots_grid('fits', xlabel='Mean [ADU]',
                                            ylabel='VARIANCE [ADU**2]',
                                            ylabel_resid='Frac. Resid.',
                                            xmin=10., xmax=250000.,
                                            ymin=10., ymax=250000,
                                            ymin_resid=-0.2, ymax_resid=0.2,
                                            xscale='log', yscale='log')

        fig_nonlin_log = figs.setup_figure("nonlin-log",
                                           xlabel="Flux [a.u.]",
                                           ylabel='Frac. Resid',
                                           figsize=(7, 5))
        axes_nonlin_log = fig_nonlin_log['axes']
        axes_nonlin_log.set_xscale('log')
        axes_nonlin_log.set_ylim(-0.06, 0.05)
        axes_nonlin_log.set_xlim(1000, 80000)

        fig_nonlin = figs.setup_figure("nonlin", xlabel="Flux [a.u.]", ylabel='Frac. Resid',
                                       figsize=(7, 5))
        axes_nonlin = fig_nonlin['axes']
        axes_nonlin.set_ylim(-0.05, 0.05)
        axes_nonlin.set_xlim(0., 80000)

        for amp in range(16):

            xvals = np.squeeze(ptc_means[amp])
            sort_idx = np.argsort(xvals)
            xvals_sorted = xvals[sort_idx]
            yvals_sorted = np.squeeze(ptc_vars[amp])[sort_idx]

            ptc_pars = (a00s[amp], gains[amp], alphas[amp])
            yvals_fit = ptc_func(ptc_pars, xvals_sorted)
            frac_resid = (yvals_sorted - yvals_fit)/yvals_fit
            mask = xvals_sorted < 8.0e4
            x_masked = xvals_sorted[mask]
            y_masked = frac_resid[mask]

            amp_plot_data = dict(xvals=xvals_sorted, yvals=yvals_sorted, resid_vals=frac_resid,
                                 model_vals=yvals_fit, body_mask=mask, resid_mask=mask)
            figs.plot_resid('fits', amp, amp_plot_data)
            axes_nonlin.plot(x_masked, y_masked, '-', label="Amp %i" % amp)
            axes_nonlin_log.plot(x_masked, y_masked, '-', label="Amp %i" % amp)


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



class PTCStatsConfig(FlatRaftTableAnalysisConfig):
    """Configuration for PTCSummaryTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='ptc')
    filekey = EOUtilOptions.clone_param('filekey', default='ptc-stats')

class PTCStatsTask(FlatRaftTableAnalysisTask):
    """Summarize the results for the analysis of variations of the
    photon transfer curves frames"""

    ConfigClass = PTCStatsConfig
    _DefaultName = "PTCStatsTask"

    # This is the list of plots, used to make sure that they exist
    plot_names = ['a00', 'alpha', 'gain']

    def extract(self, butler, data, **kwargs):
        """Extract the FFT summary statistics

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

        datakey = 'ptc'

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

        slot_list = self.config.slots
        if slot_list is None:
            slot_list = ALL_SLOTS

        remove_cols = ['ptc_mean', 'ptc_var']

        for islot, slot in enumerate(slot_list):

            basename = data[slot]

            if not os.path.exists(basename):
                self.log.warn("No file %s" % basename)
                continue

            dtables = TableDict(basename, [datakey])
            if not dtables.keys():
                self.log.warn("No tables")
                continue

            self.log_progress("  %s" % slot)
            table = dtables[datakey]


            for _ in range(16):
                for key, val in table.items():
                    if key in remove_cols:
                        continue
                    data_dict[key].append(val)
                data_dict['slot'].append(islot)

        self.log_progress("Done!")

        outtables = TableDict()
        outtables.make_datatable("ptc_stats", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the data from the bias fft statistics study

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        sumtable = dtables['ptc_stats']
        idxs = sumtable['slot']*16 + sumtable['amp']

        for plot_name in self.plot_names:
            raft_array = np.zeros((144))
            raft_array[idxs] = sumtable[plot_name]
            figs.plot_stat_color(plot_name, raft_array.reshape(9, 16))



class PTCSummaryConfig(FlatSummaryAnalysisConfig):
    """Configuration for PTCSummaryTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='ptc-stats')
    filekey = EOUtilOptions.clone_param('filekey', default='ptc-sum')


class PTCSummaryTask(FlatSummaryAnalysisTask):
    """Summarize the results for the analysis of variations of the
    photon transfer curves frames"""

    ConfigClass = PTCSummaryConfig
    _DefaultName = "PTCSummaryTask"

    plot_names = ['gain']

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


        if not self.config.skip:
            outtable = vstack_tables(data, tablename='ptc')

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

        figs.plot_run_chart("ptc-gain", runs, yvals, yerrs=yerrs, ylabel="Gain")


EO_TASK_FACTORY.add_task_class('PTC', PTCTask)
EO_TASK_FACTORY.add_task_class('PTCStats', PTCStatsTask)
EO_TASK_FACTORY.add_task_class('PTCSummary', PTCSummaryTask)
