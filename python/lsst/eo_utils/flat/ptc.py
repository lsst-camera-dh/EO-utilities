"""Class to analyze the photon transfer curve"""


import sys

import scipy.optimize

import numpy as np

import lsst.afw.math as afwMath

from lsst.eotest.sensor.ptcTask import ptc_func, residuals

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_amp_list,\
    get_geom_regions, get_raw_image, unbias_amp

from lsst.eo_utils.bias.file_utils import get_superbias_frame

from lsst.eo_utils.flat.file_utils import flat_summary_tablename, flat_summary_plotname,\
    raft_flat_tablename, raft_flat_plotname

from lsst.eo_utils.flat.analysis import FlatAnalysisBySlot, FlatAnalysisConfig,\
    FlatAnalysisTask

from lsst.eo_utils.flat.meta_analysis import FlatSummaryByRaft, FlatTableAnalysisByRaft,\
    FlatSummaryAnalysisConfig, FlatSummaryAnalysisTask


class PTCConfig(FlatAnalysisConfig):
    """Configuration for BiasVRowTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='ptc')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')
    mask = EOUtilConfig.clone_param('mask')


class PTCTask(FlatAnalysisTask):
    """Class to extract the photon transfer curve"""

    ConfigClass = PTCConfig
    _DefaultName = "PTCTask"
    iteratorClass = FlatAnalysisBySlot

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


    def extract(self, butler, data, **kwargs):
        """Extract the flat as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the flat and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        slot = kwargs['slot']

        flat_files = data['FLAT']
        mask_files = get_mask_files(self, **kwargs)
        superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

        ptc_data = dict()
        for i in range(1, 17):
            ptc_data['AMP%02i_MEAN' % (i+1)] = []
            ptc_data['AMP%02i_VAR' % (i+1)] = []

        sys.stdout.write("Working on %s, %i files: \n" % (slot, len(flat_files)))
        for id_1, id_2 in zip(flat_files[::2], flat_files[1::2]):
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

                fratio_im = afwImage.ImageF(image_1, True)
                operator.itruediv(fratio_im, image_2)
                fratio = self.mean(fratio_im)
                image_2 *= fratio
                fmean = (self.mean(image_1) + self.mean(image_2))/2.

                fdiff = afwImage.ImageF(image_1, True)
                fdiff -= image_2
                fvar = self.var(fdiff)/2.

                ptc_data['AMP%02i_MEAN' % (i+1)].append(fmean)
                ptc_data['AMP%02i_VAR' % (i+1)].append(fvar)

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
    """Configuration for BiasVRowTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='ptc_stats')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')


class PTCStatsTask(FlatAnalysisTask):
    """Class to analyze the overscan flat as a function of row number"""

    ConfigClass = PTCStatsConfig
    _DefaultName = "PTCStatsTask"
    iteratorClass = FlatTableAnalysisByRaft
    tablefile_name = raft_flat_tablename
    plotfile_name = raft_flat_plotname

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

            basename = data
            datapath = basename.replace('.fits', '_ptc.fits')

            dtables = TableDict(datapath)
            tab = dtables['ptc_stats']

            for amp in range(16):
                mean = tab["AMP%02i_MEAN" % (amp)]
                var = tab["AMP%02i_VAR" % (amp)]
                med_gain = np.median(mean/var)
                frac_resids = np.abs((var - mean/med_gain)/var)
                index = np.where(frac_resids < 0.2)
                init_pars = 0, med_gain
                try:
                    results = scipy.optimize.leastsq(residuals, init_pars, full_output=1,
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
                data_dict['amp'].append(amp)

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
    """Configuration for CorrelWRTOScanSummaryTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='_ptc_sum')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')


class PTCSummaryTask(FlatSummaryAnalysisTask):
    """Class to analyze the overscan flat as a function of row number"""

    ConfigClass = PTCSummaryConfig
    _DefaultName = "PTCSummaryTask"
    iteratorClass = FlatSummaryByRaft
    tablefile_name = flat_summary_tablename
    plotfile_name = flat_summary_plotname

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

        insuffix = '_ptc_stats.fits'

        for key, val in data.items():
            data[key] = val.replace('.fits', insuffix)

        remove_cols = ['ptc_means', 'ptc_vars']

        if not kwargs.get('skip', False):
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
