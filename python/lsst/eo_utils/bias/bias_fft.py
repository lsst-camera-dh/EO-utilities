"""Class to analyze the FFT of the bias frames"""

import sys

import numpy as np

from scipy import fftpack

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.file_utils import SUPERBIAS_FORMATTER

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    get_readout_freqs_from_ccd, get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp

from lsst.eo_utils.base.iter_utils import TableAnalysisBySlot,\
    TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .file_utils import SLOT_BIAS_TABLE_FORMATTER,\
    SLOT_SBIAS_TABLE_FORMATTER, SLOT_SBIAS_PLOT_FORMATTER,\
    RAFT_BIAS_TABLE_FORMATTER, RAFT_BIAS_PLOT_FORMATTER

from .analysis import BiasAnalysisConfig, BiasAnalysisTask

from .meta_analysis import BiasSummaryAnalysisConfig, BiasSummaryAnalysisTask


class BiasFFTConfig(BiasAnalysisConfig):
    """Configuration for BiasFFTTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasfft')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')


class BiasFFTTask(BiasAnalysisTask):
    """Analyze the FFT of the bias frames"""

    ConfigClass = BiasFFTConfig
    _DefaultName = "BiasFFTTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the FFT of the bias as function of row

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

        slot = self.config.slot

        bias_files = data['BIAS']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        fft_data = {}

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)
            if ifile == 0:
                freqs_dict = get_readout_freqs_from_ccd(butler, ccd)
            for key in REGION_KEYS:
                freqs = freqs_dict['freqs_%s' % key]
                nfreqs = len(freqs)
                fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])

            self.get_ccd_data(butler, ccd, fft_data,
                              ifile=ifile, nfiles_used=len(bias_files),
                              slot=slot, superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the FFT of the bias as function of row

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

        for key, region in zip(REGION_KEYS, REGION_NAMES):
            datakey = 'biasfft-%s' % key
            figs.setup_amp_plots_grid(datakey, title="FFT of %s region mean by row" % region,
                                      xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]",
                                      ymin=0., ymax=3.)
            figs.plot_xy_amps_from_tabledict(dtables, datakey, datakey,
                                             x_name='freqs', y_name='fftpow',
                                             ymin=0., ymax=3.)


    def get_ccd_data(self, butler, ccd, data, **kwargs):
        """Get the fft of the overscan values and update the data dictionary

        Parameters
        ----------
        butler : `Butler`
            The data butler
        ccd : `MaskedCCD`
            The ccd we are getting data from
        data : `dict`
            The data we are updating

        Keywords
        --------
        slot : `str`
            The slot name
        ifile : `int`
            The file index
        nfiles_used : `int`
            Total number of files
        bias_type : `str`
            Method to use to construct bias
        std : `bool`
            Used standard deviation instead of mean
        superbias_frame : `MaskedCCD`
            The superbias frame to subtract away
        """
        self.safe_update(**kwargs)

        slot = kwargs['slot']
        ifile = kwargs.get('ifile', 0)
        nfiles_used = kwargs.get('nfiles_used', 1)
        superbias_frame = kwargs.get('superbias_frame', None)

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(butler, ccd, amp)
            if superbias_frame is not None:
                if butler is not None:
                    superbias_im = get_raw_image(None, superbias_frame, amp+1)
                else:
                    superbias_im = get_raw_image(None, superbias_frame, amp)
            else:
                superbias_im = None
            image = unbias_amp(img, serial_oscan,
                               bias_type=self.get_config_param('bias', None),
                               superbias_im=superbias_im)
            frames = get_image_frames_2d(image, regions)
            key_str = "fftpow_%s_a%02i" % (slot, i)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                struct = array_struct(frames[region], do_std=self.config.std)
                fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
                nval = len(fftpow)
                fftpow /= nval/2
                if key_str not in data[key]:
                    data[key][key_str] = np.ndarray((int(nval/2), nfiles_used))
                data[key][key_str][:, ifile] = np.sqrt(fftpow[0:int(nval/2)])



class SuperbiasFFTConfig(BiasFFTConfig):
    """Configuration for SuperbiasFFTTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='sbiasfft')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')


class SuperbiasFFTTask(BiasFFTTask):
    """Analyze the FFT of the superbias frames"""

    ConfigClass = SuperbiasFFTConfig
    _DefaultName = "SuperbiasFFTTask"
    iteratorClass = TableAnalysisBySlot

    intablename_format = SUPERBIAS_FORMATTER
    tablename_format = SLOT_SBIAS_TABLE_FORMATTER
    plotname_format = SLOT_SBIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasFFTTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the FFTs of the row-wise and col-wise struture
        in a superbias frame

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
        slot = self.config.slot

        if butler is not None:
            sys.stdout.write("Ignoring butler in extract_superbias_fft_slot\n")

        mask_files = self.get_mask_files()
        superbias_file = data[0] + '.fits'
        superbias = get_ccd_from_id(None, superbias_file, mask_files)

        fft_data = {}

        freqs_dict = get_readout_freqs_from_ccd(None, superbias)
        for key in REGION_KEYS:
            freqs = freqs_dict['freqs_%s' % key]
            nfreqs = len(freqs)
            fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])

        self.get_ccd_data(None, superbias, fft_data,
                          slot=slot, superbias_frame=None)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])
        return dtables


class BiasFFTStatsConfig(BiasAnalysisConfig):
    """Configuration for BiasFFTStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='biasfft')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasfft_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class BiasFFTStatsTask(BiasAnalysisTask):
    """Extract statistics about the FFT of the bias frames"""

    ConfigClass = BiasFFTStatsConfig
    _DefaultName = "BiasAnalysisTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_BIAS_TABLE_FORMATTER
    tablename_format = RAFT_BIAS_TABLE_FORMATTER
    plotname_format = RAFT_BIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasAnalysisTask.__init__(self, **kwargs)


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
            sys.stdout.write("Ignoring butler in bias_fft_stats.extract\n")

        datakey = 'biasfft-s'

        data_dict = dict(fftpow_mean=[],
                         fftpow_median=[],
                         fftpow_std=[],
                         fftpow_min=[],
                         fftpow_max=[],
                         fftpow_maxval=[],
                         fftpow_argmax=[],
                         slot=[],
                         amp=[])

        freqs = None

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace('_biasfft_stats.fits', '_biasfft.fits')

            dtables = TableDict(datapath, [datakey])
            table = dtables[datakey]

            if freqs is None:
                freqs = table['freqs']

            for amp in range(16):
                tablevals = table['fftpow_%s_a%02i' % (slot, amp)]
                meanvals = np.mean(tablevals, axis=1)
                data_dict['fftpow_mean'].append(meanvals)
                data_dict['fftpow_median'].append(np.median(tablevals, axis=1))
                data_dict['fftpow_std'].append(np.std(tablevals, axis=1))
                data_dict['fftpow_min'].append(np.min(tablevals, axis=1))
                data_dict['fftpow_max'].append(np.max(tablevals, axis=1))
                data_dict['fftpow_maxval'].append(meanvals[100:].max())
                data_dict['fftpow_argmax'].append(meanvals[100:].argmax())
                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("freqs", dict(freqs=freqs))
        outtables.make_datatable("biasfft_stats", data_dict)
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
        sumtable = dtables['biasfft_stats']
        figs.plot_stat_color('max_fft_noise', sumtable['fftpow_maxval'].reshape(9, 16))



class BiasFFTSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for BiasFFTSummaryTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='biasfft_stats')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasfft_sum')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')


class BiasFFTSummaryTask(BiasSummaryAnalysisTask):
    """Summarize the results for the analysis of the FFT of the bias frames"""

    ConfigClass = BiasFFTSummaryConfig
    _DefaultName = "BiasFFTSummaryTask"

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasSummaryAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Make a summry table of the bias FFT data

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
            sys.stdout.write("Ignoring butler in bias_fft_summary.extract\n")

        for key, val in data.items():
            data[key] = val.replace('_biasfft_sum.fits', '_biasfft_stats.fits')

        keep_cols = ['fftpow_maxval', 'fftpow_argmax', 'slot', 'amp']

        outtable = vstack_tables(data, tablename='biasfft_stats', keep_cols=keep_cols)

        dtables = TableDict()
        dtables.add_datatable('biasfft_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the superbias statistics study

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

        sumtable = dtables['biasfft_sum']
        runtable = dtables['runs']

        yvals = sumtable['fftpow_maxval'].flatten().clip(0., 2.)
        runs = runtable['runs']

        figs.plot_run_chart("fftpow_maxval", runs, yvals, ylabel="Maximum FFT Power [ADU]")


EO_TASK_FACTORY.add_task_class('BiasFFT', BiasFFTTask)
EO_TASK_FACTORY.add_task_class('SuperbiasFFT', SuperbiasFFTTask)
EO_TASK_FACTORY.add_task_class('BiasFFTStats', BiasFFTStatsTask)
EO_TASK_FACTORY.add_task_class('BiasFFTSummary', BiasFFTSummaryTask)
