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
    """Configuration for PTCTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='ptc')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class PTCTask(FlatAnalysisTask):
    """Extract the photon transfer curve"""

    ConfigClass = PTCConfig
    _DefaultName = "PTCTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor"""
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
        """Extract the flat as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the flat and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        flat1_files = data['FLAT1']
        flat2_files = data['FLAT2']
        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        ptc_data = dict()
        for i in range(1, 17):
            ptc_data['AMP%02i_MEAN' % i] = []
            ptc_data['AMP%02i_VAR' % i] = []

        sys.stdout.write("Working on %s, %i files: \n" % (self.config.slot, len(flat1_files)))
        for id_1, id_2 in zip(flat1_files, flat2_files):
            flat_1 = get_ccd_from_id(butler, id_1, [])
            flat_2 = get_ccd_from_id(butler, id_2, [])

            amps = get_amp_list(butler, flat_1)

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

                ptc_data['AMP%02i_MEAN' % (i+1)].append(fstats[1])
                ptc_data['AMP%02i_VAR' % (i+1)].append(fstats[2])

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, flat_files))
        dtables.make_datatable('ptc', ptc_data)

        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the ptc statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)

        if dtables is not None and figs is not None:
            sys.stdout.write('No plots defined for ptc_analysis\n')


class PTCStatsConfig(FlatAnalysisConfig):
    """Configuration for PTCStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='ptc')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='ptc_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class PTCStatsTask(FlatAnalysisTask):
    """Extract statistics about the photon transfer curves"""

    ConfigClass = PTCStatsConfig
    _DefaultName = "PTCStatsTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_FLAT_TABLE_FORMATTER
    tablename_format = RAFT_FLAT_TABLE_FORMATTER
    plotname_format = RAFT_FLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor """
        FlatAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract the flat as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the flat and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        if butler is not None:
            sys.stdout.write("Ignoring butler in ptc_stats.extract\n")

        data_dict = dict(npts=[],
                         nused=[],
                         ptc_mean=[],
                         ptc_var=[],
                         med_gain=[],
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

            dtables = TableDict(data[slot].replace('ptc_stats.fits', 'ptc.fits'))
            tab = dtables['ptc_stats']

            for amp in range(1, 17):
                mean = tab["AMP%02i_MEAN" % (amp)]
                var = tab["AMP%02i_VAR" % (amp)]
                med_gain = np.median(mean/var)
                frac_resids = np.abs((var - mean/med_gain)/var)
                index = np.where(frac_resids < 0.2)
                try:
                    results = scipy.optimize.leastsq(residuals, (0, med_gain), full_output=1,
                                                     args=(mean[index], var[index]))
                    pars, cov = results[:2]
                    ptc_alpha = pars[0]
                    ptc_alpha_error = np.sqrt(cov[0][0])
                    ptc_gain = pars[1]
                    ptc_gain_error = np.sqrt(cov[1][1])
                except Exception as eobj:
                    sys.stderr.write("Exception caught while fitting PTC:")
                    sys.stderr.write(str(eobj))
                    sys.stderr.write("\n")
                    ptc_gain = 0.
                    ptc_gain_error = -1.
                    ptc_alpha = 0.
                    ptc_alpha_error = -1.
                data_dict['ptc_mean'].append(mean)
                data_dict['ptc_var'].append(var)
                data_dict['npts'].append(mean.size)
                data_dict['nused'].append(len(index))
                data_dict['med_gain'].append(med_gain)
                data_dict['alpha'].append(ptc_alpha)
                data_dict['alpha_error'].append(ptc_alpha_error)
                data_dict['gain'].append(ptc_gain)
                data_dict['gain_error'].append(ptc_gain_error)
                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp-1)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("ptc_stats", data_dict)
        return outtables


    @staticmethod
    def plot_fits(dtables, figs):
        """Plot the amplifier by amplifier fits from the ptc study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        table = dtables['ptc_stats']
        ptc_means = table['ptc_mean']
        ptc_vars = table['ptc_var']
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
                ptc_pars = (alphas[idx], gains[idx])
                yvals = ptc_func(ptc_pars, xvals)
                axes.plot(xvals, yvals, 'r-')
                idx += 1

    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the ptc statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)
        self.plot_fits(dtables, figs)

        #sumtable = dtables['ptc_stats']
        #figs.plot_stat_color('gain_array', sumtable['gain'].reshape(9,16))


class PTCSummaryConfig(FlatSummaryAnalysisConfig):
    """Configuration for PTCSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='ptc_stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='ptc_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class PTCSummaryTask(FlatSummaryAnalysisTask):
    """Summarize the results for the analysis of variations of the
    photon transfer curves frames"""

    ConfigClass = PTCSummaryConfig
    _DefaultName = "PTCSummaryTask"

    def __init__(self, **kwargs):
        """C'tor"""
        FlatSummaryAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Make a summry table of the flat FFT data

        @param filedict (dict)      The files we are analyzing
        @param kwargs

        @returns (TableDict)
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
        """Plot the summary data from the superflat statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)
        sumtable = dtables['ptc_sum']
        runtable = dtables['runs']

        yvals = sumtable['gain'].flatten().clip(0., 2.)
        yerrs = sumtable['gain_error'].flatten().clip(0., 0.5)
        runs = runtable['runs']

        figs.plot_run_chart("ptc_gain", runs, yvals, yerrs=yerrs, ylabel="Gain")


EO_TASK_FACTORY.add_task_class('PTC', PTCTask)
EO_TASK_FACTORY.add_task_class('PTCStats', PTCStatsTask)
EO_TASK_FACTORY.add_task_class('PTCSummary', PTCSummaryTask)
