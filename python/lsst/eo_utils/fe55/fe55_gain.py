"""Class to analyze the gains from fe55 cluster fitting"""

import numpy as np

from lsst.eotest.sensor import Fe55GainFitter

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.fe55.meta_analysis import Fe55RaftTableAnalysisConfig,\
    Fe55RaftTableAnalysisTask,\
    Fe55SummaryAnalysisConfig, Fe55SummaryAnalysisTask


class Fe55GainStatsConfig(Fe55RaftTableAnalysisConfig):
    """Configuration for Fe55GainStatsTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='fe55-clusters')
    filekey = EOUtilOptions.clone_param('filekey', default='fe55-gain-stats')
    use_all = EOUtilOptions.clone_param('use_all')


class Fe55GainStatsTask(Fe55RaftTableAnalysisTask):
    """Analyze the gains using the fe55 cluster fit results"""

    ConfigClass = Fe55GainStatsConfig
    _DefaultName = "Fe55GainStatsTask"

    plot_names = ['gain']

    def extract(self, butler, data, **kwargs):
        """Extract the gains and widths from the f355 clusters

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

        use_all = self.config.use_all

        data_dict = dict(kalpha_peak=[],
                         kalpha_sigma=[],
                         ncluster=[],
                         ngood=[],
                         gain=[],
                         gain_error=[],
                         fit_xmin=[],
                         fit_xmax=[],
                         fit_pars=[],
                         fit_nbins=[],
                         sigmax_median=[],
                         sigmay_median=[],
                         slot=[],
                         amp=[])

        self.log_info_raft_msg(self.config, "")

        for islot, slot in enumerate(ALL_SLOTS):

            self.log_progress("  %s" % slot)

            basename = data[slot]

            dtables = TableDict(basename)

            for amp in range(16):
                table = dtables['amp%02i' % (amp+1)]
                if use_all:
                    mask = np.ones((len(table)), bool)
                else:
                    mask = (np.fabs(table['XPOS'] - table['XPEAK']) < 1)*\
                        (np.fabs(table['YPOS'] - table['YPEAK']) < 1)
                tablevals = table[mask]['DN']
                gainfitter = Fe55GainFitter(tablevals)
                try:
                    kalpha_peak, kalpha_sigma = gainfitter.fit(bins=100)
                    gain = gainfitter.gain
                    gain_error = gainfitter.gain_error
                    pars = gainfitter.pars
                except Exception:
                    kalpha_peak, kalpha_sigma = (np.nan, np.nan)
                    gain = np.nan
                    gain_error = np.nan
                    pars = np.nan * np.ones((4))
                data_dict['kalpha_peak'].append(kalpha_peak)
                data_dict['kalpha_sigma'].append(kalpha_sigma)
                data_dict['gain'].append(gain)
                data_dict['gain_error'].append(gain_error)
                xra = gainfitter.xrange
                data_dict['ncluster'].append(mask.size)
                data_dict['ngood'].append(mask.sum())
                if xra is None:
                    data_dict['fit_xmin'].append(np.nan)
                    data_dict['fit_xmax'].append(np.nan)
                else:
                    data_dict['fit_xmin'].append(xra[0])
                    data_dict['fit_xmax'].append(xra[1])
                data_dict['fit_pars'].append(pars)
                data_dict['fit_nbins'].append(100.)
                data_dict['sigmax_median'].append(np.median(table['SIGMAX']))
                data_dict['sigmay_median'].append(np.median(table['SIGMAY']))
                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        self.log_progress("Done!")

        outtables = TableDict()
        outtables.make_datatable("fe55_gain_stats", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the gain results from the fe55 study

        It should use a `TableDict` object to create a set of
        plots and fill a `FigureDict` object

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
        sumtable = dtables['fe55_gain_stats']
        figs.plot_stat_color('gain', sumtable['gain'].reshape(9, 16))



class Fe55GainSummaryConfig(Fe55SummaryAnalysisConfig):
    """Configuration for Fe55GainSummaryTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='fe55-gain-stats')
    filekey = EOUtilOptions.clone_param('filekey', default='fe55-gain-sum')
    use_all = EOUtilOptions.clone_param('use_all')


class Fe55GainSummaryTask(Fe55SummaryAnalysisTask):
    """Sumarize the results of the Fe55 gain analyses"""

    ConfigClass = Fe55GainSummaryConfig
    _DefaultName = "Fe55GainSummaryTask"

    plot_names = ['gain', 'sigmax', 'fgood']

    def extract(self, butler, data, **kwargs):
        """Make a summry table of the fe55 data

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
            data[key] = val.replace('_fe55-gain-sum.fits', '_fe55-gain-stats.fits')

        remove_cols = ['fit_pars']

        if not self.config.skip:
            outtable = vstack_tables(data, tablename='fe55_gain_stats',
                                     remove_cols=remove_cols)

        dtables = TableDict()
        dtables.add_datatable('fe55_gain_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the fe55 study

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
        sumtable = dtables['fe55_gain_sum']
        runtable = dtables['runs']

        yvals = sumtable['gain'].flatten().clip(0., 2.)
        yerrs = sumtable['gain_error'].flatten().clip(0., 0.5)
        runs = runtable['runs']

        figs.plot_run_chart("gain", runs, yvals, yerrs=yerrs, ylabel="Gain")

        yvals = sumtable['sigmax_median'].flatten().clip(0., 2.)
        figs.plot_run_chart("sigmax", runs, yvals, ylabel="Cluster width [pixels]")

        yvals = sumtable['ngood']/sumtable['ncluster']
        figs.plot_run_chart("fgood", runs, yvals, ylabel="Fraction of good clusters")


EO_TASK_FACTORY.add_task_class('Fe55GainStats', Fe55GainStatsTask)
EO_TASK_FACTORY.add_task_class('Fe55GainSummary', Fe55GainSummaryTask)
