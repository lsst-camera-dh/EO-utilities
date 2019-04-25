"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from scipy import fftpack

from lsst.eo_utils.base.defaults import ALL_SLOTS, DEFAULT_BIAS_TYPE

from lsst.eo_utils.base.config_utils import EOUtilConfig

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    get_readout_freqs_from_ccd, get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp

from .file_utils import get_superbias_frame,\
    slot_superbias_tablename, slot_superbias_plotname,\
    bias_summary_tablename, bias_summary_plotname,\
    raft_bias_tablename, raft_bias_plotname

from .analysis import BiasAnalysisConfig, BiasAnalysisTask, BiasAnalysisBySlot

from .meta_analysis import BiasSummaryByRaft, BiasTableAnalysisByRaft,\
    BiasSummaryAnalysisConfig, BiasSummaryAnalysisTask


class BiasFFTConfig(BiasAnalysisConfig):
    """Configuration for BiasFFTTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='biasfft')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')
    mask = EOUtilConfig.clone_param('mask')
    std = EOUtilConfig.clone_param('std')


class BiasFFTTask(BiasAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = BiasFFTConfig
    _DefaultName = "BiasFFTTask"
    iteratorClass = BiasAnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor """
        BiasAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the bias as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs
            slot (str)           Slot in question, i.e., 'S00'
            bias (str)           Method to use for unbiasing

        @returns (TableDict) with the extracted data
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        bias_files = data['BIAS']
        mask_files = get_mask_files(self, **kwargs)
        superbias_frame = get_superbias_frame(self, mask_files=mask_files, **kwargs)

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
                              ifile=ifile, nfiles=len(bias_files),
                              slot=slot, bias_type=self.config.bias,
                              std=self.config.std, superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the bias as function of row

        @param dtables (`TableDict`)  The data
        @param figs (`FigureDict`)    Object to store the figues
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

    @staticmethod
    def get_ccd_data(butler, ccd, data, **kwargs):

        """Get the fft of the overscan values and update the data dictionary

        @param butler (`Butler`)   The data butler
        @param ccd (`MaskedCCD`)   The ccd we are getting data from
        @param data (dict)         The data we are updatign
        @param kwargs:
            slot  (str)                 The slot number
            ifile (int)                 The file index
            nfiles (int)                Total number of files
            bias_type (str)             Method to use to construct bias
            std (str)                   Do standard deviation instead of mean
            superbias_frame (MaskedCCD) The superbias
        """
        slot = kwargs['slot']
        bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
        ifile = kwargs.get('ifile', 0)
        nfiles = kwargs.get('nfiles', 1)
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
            image = unbias_amp(img, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
            frames = get_image_frames_2d(image, regions)
            key_str = "fftpow_%s_a%02i" % (slot, i)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                struct = array_struct(frames[region], do_std=kwargs.get('std', False))
                fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
                nval = len(fftpow)
                fftpow /= nval/2
                if key_str not in data[key]:
                    data[key][key_str] = np.ndarray((int(nval/2), nfiles))
                data[key][key_str][:, ifile] = np.sqrt(fftpow[0:int(nval/2)])



class SuperbiasFFTConfig(BiasAnalysisConfig):
    """Configuration for BiasFFTTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='sbiasfft')
    superbias = EOUtilConfig.clone_param('superbias')
    mask = EOUtilConfig.clone_param('mask')


class SuperbiasFFTTask(BiasFFTTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = SuperbiasFFTConfig
    _DefaultName = "SuperbiasFFTTask"
    iteratorClass = BiasAnalysisBySlot

    tablefile_name = slot_superbias_tablename
    plotfile_name = slot_superbias_plotname

    def __init__(self, **kwargs):
        BiasFFTTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the FFTs of the row-wise and col-wise struture
        in a superbias frame

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the bias and mask files
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            run_num (str)        Run number, i.e,. '6106D'
            slot (str)           Slot in question, i.e., 'S00'
            superbias (str)      Method to use for superbias subtraction
            outdir (str)         Output directory
            std (bool)           Plot standard deviation instead of median
        """
        self.safe_update(**kwargs)
        slot = self.config.slot

        if butler is not None:
            sys.stdout.write("Ignoring butler in extract_superbias_fft_slot")
        if data is not None:
            sys.stdout.write("Ignoring raft_data in extract_superbias_fft_raft")

        mask_files = get_mask_files(self, **kwargs)
        superbias = get_superbias_frame(self, mask_files=mask_files, **kwargs)

        fft_data = {}

        freqs_dict = get_readout_freqs_from_ccd(None, superbias)
        for key in REGION_KEYS:
            freqs = freqs_dict['freqs_%s' % key]
            nfreqs = len(freqs)
            fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])

        self.get_ccd_data(None, superbias, fft_data,
                          slot=slot, bias_type=None,
                          std=False, superbias_frame=None)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])
        return dtables


class BiasFFTStatsConfig(BiasAnalysisConfig):
    """Configuration for OscanAmpStackStatsTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='biasfft_stats')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')



class BiasFFTStatsTask(BiasAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = BiasFFTStatsConfig
    _DefaultName = "BiasAnalysisTask"
    iteratorClass = BiasTableAnalysisByRaft
    tablefile_name = raft_bias_tablename
    plotfile_name = raft_bias_plotname

    def __init__(self, **kwargs):
        """C'tor """
        BiasAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract the bias as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
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
        """Plot the summary data from the bias fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        sumtable = dtables['biasfft_stats']
        figs.plot_stat_color('max_fft_noise', sumtable['fftpow_maxval'].reshape(9, 16))



class BiasFFTSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for CorrelWRTOScanSummaryTask"""
    suffix = EOUtilConfig.clone_param('suffix', default='biasfft_sum')
    bias = EOUtilConfig.clone_param('bias')
    superbias = EOUtilConfig.clone_param('superbias')


class BiasFFTSummaryTask(BiasSummaryAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = BiasFFTSummaryConfig
    _DefaultName = "BiasFFTSummaryTask"
    iteratorClass = BiasSummaryByRaft
    tablefile_name = bias_summary_tablename
    plotfile_name = bias_summary_plotname

    def __init__(self, **kwargs):
        """C'tor"""
        BiasSummaryAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Make a summry table of the bias FFT data

        @param filedict (dict)      The files we are analyzing
        @param kwargs
            bias (str)
            superbias (str)

        @returns (TableDict)
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

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        self.safe_update(**kwargs)

        sumtable = dtables['biasfft_sum']
        runtable = dtables['runs']

        yvals = sumtable['fftpow_maxval'].flatten().clip(0., 2.)
        runs = runtable['runs']

        figs.plot_run_chart("fftpow_maxval", runs, yvals, ylabel="Maximum FFT Power [ADU]")
