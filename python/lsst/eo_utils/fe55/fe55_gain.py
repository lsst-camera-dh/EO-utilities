"""Class to analyze the gains from fe55 cluster fitting"""

import sys

import numpy as np

from lsst.eotest.sensor import Fe55GainFitter

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.fe55.file_utils import RAFT_FE55_TABLE_FORMATTER,\
    RAFT_FE55_PLOT_FORMATTER

from lsst.eo_utils.fe55.analysis import Fe55AnalysisConfig, Fe55AnalysisTask

from lsst.eo_utils.fe55.meta_analysis import Fe55SummaryByRaft, Fe55TableAnalysisByRaft,\
    Fe55SummaryAnalysisConfig, Fe55SummaryAnalysisTask


class Fe55GainStatsConfig(Fe55AnalysisConfig):
    """Configuration for Fe55GainStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='fe55_clusters')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='fe55_gain_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    use_all = EOUtilOptions.clone_param('use_all')


class Fe55GainStatsTask(Fe55AnalysisTask):
    """Analyze the gains using the fe55 cluster fit results"""

    ConfigClass = Fe55GainStatsConfig
    _DefaultName = "Fe55GainStatsTask"
    iteratorClass = Fe55TableAnalysisByRaft

    tablename_format = RAFT_FE55_TABLE_FORMATTER
    plotname_format = RAFT_FE55_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor """
        Fe55AnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the fe55 as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the fe55 and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        if butler is not None:
            sys.stdout.write("Ignoring butler in fe55_gain_stats.extract\n")

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

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace('fe55_gain_stats.fits', 'fe55_clusters.fits')

            dtables = TableDict(datapath)

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

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("fe55_gain_stats", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the fe55 fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)
        sumtable = dtables['fe55_gain_stats']
        figs.plot_stat_color('gain_array', sumtable['gain'].reshape(9, 16))



class Fe55GainSummaryConfig(Fe55SummaryAnalysisConfig):
    """Configuration for Fe55GainSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='fe55_gain_stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='fe55_gain_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    use_all = EOUtilOptions.clone_param('use_all')


class Fe55GainSummaryTask(Fe55SummaryAnalysisTask):
    """Sumarize the results of the Fe55 gain analyses"""

    ConfigClass = Fe55GainSummaryConfig
    _DefaultName = ""
    iteratorClass = Fe55SummaryByRaft

    def __init__(self, **kwargs):
        """C'tor"""
        Fe55SummaryAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Make a summry table of the fe55 FFT data

        @param filedict (dict)      The files we are analyzing
        @param kwargs

        @returns (TableDict)
        """
        self.safe_update(**kwargs)

        if butler is not None:
            sys.stdout.write("Ignoring butler in fe55_gain_summary.extract\n")

        for key, val in data.items():
            data[key] = val.replace('_fe55_gain_sum.fits', '_fe55_gain_stats.fits')

        remove_cols = ['fit_pars']

        if not self.config.skip:
            outtable = vstack_tables(data, tablename='fe55_gain_stats',
                                     remove_cols=remove_cols)

        dtables = TableDict()
        dtables.add_datatable('fe55_gain_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the superfe55 statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)
        sumtable = dtables['fe55_gain_sum']
        runtable = dtables['runs']

        yvals = sumtable['gain'].flatten().clip(0., 2.)
        yerrs = sumtable['gain_error'].flatten().clip(0., 0.5)
        runs = runtable['runs']

        figs.plot_run_chart("fe55_gain", runs, yvals, yerrs=yerrs, ylabel="Gain")

        yvals = sumtable['sigmax_median'].flatten().clip(0., 2.)
        figs.plot_run_chart("fe55_sigmax", runs, yvals, ylabel="Cluster width [pixels]")

        yvals = sumtable['ngood']/sumtable['ncluster']
        figs.plot_run_chart("fe55_fgood", runs, yvals, ylabel="Fraction of good clusters")


EO_TASK_FACTORY.add_task_class('Fe55GainStats', Fe55GainStatsTask)
EO_TASK_FACTORY.add_task_class('Fe55GainSummary', Fe55GainSummaryTask)
