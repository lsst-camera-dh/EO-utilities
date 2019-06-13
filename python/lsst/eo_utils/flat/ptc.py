"""Class to analyze the photon transfer curve"""


import sys

import operator

import scipy.optimize

import numpy as np

import lsst.afw.math as afwMath

import lsst.afw.image as afwImage

from lsst.eotest.sensor.ptcTask import ptc_func, residuals

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_amp_list,\
    get_geom_regions, get_raw_image, unbias_amp

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig,\
    FlatAnalysisTask

from lsst.eo_utils.flat.meta_analysis import FlatSummaryAnalysisConfig, FlatSummaryAnalysisTask


class PTCConfig(FlatAnalysisConfig):
    """Configuration for PTCStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='flat')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='ptc')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class PTCTask(FlatAnalysisTask):
    """Extract statistics about the photon transfer curves"""

    ConfigClass = PTCConfig
    _DefaultName = "PTCTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_FLAT_TABLE_FORMATTER
    tablename_format = RAFT_FLAT_TABLE_FORMATTER
    plotname_format = RAFT_FLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        FlatAnalysisTask.__init__(self, **kwargs)


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
            sys.stdout.write("Ignoring butler in ptc_stats.extract\n")

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

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            dtables = TableDict(data[slot].replace('ptc.fits', 'flat.fits'))
            tab = dtables['flat']

            for amp in range(1, 17):
                mean = tab["AMP%02i_MEAN" % (amp)]
                var = tab["AMP%02i_VAR" % (amp)]
                med_gain = np.median(mean/var)
                frac_resids = np.abs((var - mean/med_gain)/var)
                index = np.where(frac_resids < 0.2)
                try:
                    results = scipy.optimize.leastsq(residuals, (1., med_gain, 0.), full_output=1,
                                                     args=(mean[index], var[index]))
                    pars, cov = results[:2]
                    ptc_a00 = pars[0]
                    ptc_a00_error = np.sqrt(cov[0][0])
                    ptc_alpha = pars[1]
                    ptc_alpha_error = np.sqrt(cov[1][1])
                    ptc_gain = pars[2]
                    ptc_gain_error = np.sqrt(cov[2][2])
                except Exception as eobj:
                    sys.stderr.write("Exception caught while fitting PTC:")
                    sys.stderr.write(str(eobj))
                    sys.stderr.write("\n")
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

        sys.stdout.write(".\n")
        sys.stdout.flush()

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

        log_xmins = np.log10(ptc_means[:, 0])
        log_xmaxs = np.log10(ptc_means[:, -1])

        idx = 0
        for slot in ALL_SLOTS:
            figs.setup_amp_plots_grid(slot, xlabel="Mean [ADU]", ylabel="Var [ADU**2]")
            for amp in range(16):
                axes = figs.get_amp_axes(slot, amp)
                axes.set_xscale('log')
                axes.set_yscale('log')
                axes.scatter(ptc_means[idx], ptc_vars[idx])
                xvals = np.logspace(log_xmins[idx], log_xmaxs[idx], 100)
                ptc_pars = (a00s[idx], gains[idx], alphas[idx])
                yvals = ptc_func(ptc_pars, xvals)
                axes.plot(xvals, yvals, 'r-')
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

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        FlatSummaryAnalysisTask.__init__(self, **kwargs)


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
            sys.stdout.write("Ignoring butler in ptc_summary.extract\n")

        for key, val in data.items():
            data[key] = val.replace('_ptc_sum.fits', '_ptc_stats.fits')

        remove_cols = ['ptc_mean', 'ptc_var']

        if not self.config.skip:
            outtable = vstack_tables(data, tablename='ptc_stats',
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
