"""Class to analyze the FFT of the bias frames"""

import os

import numpy as np

from scipy import fftpack

from lsst.eo_utils.base.defaults import ALL_SLOTS, getSlotList

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables,\
    get_run_config_table

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    raw_amp_image, get_readout_freqs_from_ccd, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp,\
    get_amp_offset

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .analysis import BiasAnalysisConfig, BiasAnalysisTask

from .meta_analysis import BiasRaftTableAnalysisConfig, BiasRaftTableAnalysisTask,\
    BiasSummaryAnalysisConfig, BiasSummaryAnalysisTask,\
    BiasRunTableAnalysisConfig, BiasRunTableAnalysisTask,\
    SuperbiasSlotTableAnalysisConfig, SuperbiasSlotTableAnalysisTask


class BiasFFTConfig(BiasAnalysisConfig):
    """Configuration for BiasFFTTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='biasfft')
    std = EOUtilOptions.clone_param('std')


class BiasFFTTask(BiasAnalysisTask):
    """Analyze the FFT of the bias frames"""

    ConfigClass = BiasFFTConfig
    _DefaultName = "BiasFFTTask"
    iteratorClass = AnalysisBySlot

    # This is the list of plots, used to make sure that they exist
    plot_names = ['i', 'p', 's', 'i-col', 's-col', 'p-col']

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

        if not bias_files:
            self.log_info_slot_msg(self.config, "No bias data, skipping")
            return None

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(bias_files))

        fft_data = {}

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            ccd = self.get_ccd(butler, bias_file, mask_files)
            if ifile == 0:
                freqs_dict = get_readout_freqs_from_ccd(ccd)

            for key in REGION_KEYS:
                freqs = freqs_dict['freqs_%s' % key]
                freqs_col = freqs_dict['freqs_%s_col' % key]
                nfreqs = len(freqs)
                nfreqs_col = len(freqs_col)
                if key not in fft_data:
                    fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])
                    fft_data["%s_col" % key] = dict(freqs=freqs_col[0:int(nfreqs_col/2)])

            BiasFFTTask.get_ccd_data(self, ccd, fft_data,
                                     ifile=ifile, nfiles_used=len(bias_files),
                                     slot=slot, superbias_frame=superbias_frame)

        self.log_progress("Done!")

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])
            dtables.make_datatable('biasfft-%s_col' % key, fft_data["%s_col" % key])

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

        if not dtables.keys():
            return

        for key, region in zip(REGION_KEYS, REGION_NAMES):
            datakey = 'biasfft-%s' % key
            figs.setup_amp_plots_grid(key, title="FFT of %s region mean by row" % region,
                                      xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
            figs.plot_xy_amps_from_tabledict(dtables, datakey, key,
                                             x_name='freqs', y_name='fftpow')
            datakey_col = "biasfft-%s_col" % key
            figs.setup_amp_plots_grid("%s-col" % key, title="FFT of %s region columns" % region,
                                      xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
            figs.plot_xy_amps_from_tabledict(dtables, datakey_col, "%s-col" % key,
                                             x_name='freqs', y_name='fftpow')


    @staticmethod
    def get_ccd_data(for_whom, ccd, data, **kwargs):
        """Get the fft of the overscan values and update the data dictionary

        Parameters
        ----------
        for_whom : `Task`
            Task this is being run for
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
        for_whom.safe_update(**kwargs)
        bias_type = for_whom.get_bias_algo()

        slot = kwargs['slot']
        ifile = kwargs.get('ifile', 0)
        nfiles_used = kwargs.get('nfiles_used', 1)
        superbias_frame = kwargs.get('superbias_frame', None)

        amps = get_amp_list(ccd)
        offset = get_amp_offset(ccd, superbias_frame)

        for i, amp in enumerate(amps):
            regions = get_geom_regions(ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(ccd, amp)
            superbias_im = raw_amp_image(superbias_frame, amp + offset)
            image = unbias_amp(img, serial_oscan,
                               bias_type=bias_type,
                               superbias_im=superbias_im)
            frames = get_image_frames_2d(image, regions)
            key_str = "fftpow_%s_a%02i" % (slot, i)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                key_col = "%s_col" % key
                struct = array_struct(frames[region], do_std=for_whom.config.std)
                fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
                nval = len(fftpow)
                fftpow /= nval/2
                if key_str not in data[key]:
                    data[key][key_str] = np.zeros((int(nval/2), nfiles_used))
                data[key][key_str][:, ifile] = np.sqrt(fftpow[0:int(nval/2)])

                fft_by_col = []
                for row_data in frames[region]:
                    fftpow_row = np.abs(fftpack.fft(row_data-row_data.mean()))
                    nvals = len(fftpow_row)
                    fftpow_row /= nvals/2
                    fft_by_col.append(fftpow_row[0:int(nvals/2)])
                fft_mean_by_col = np.sqrt(np.vstack(fft_by_col)).mean(axis=0)
                if key_str not in data[key_col]:
                    data[key_col][key_str] = np.zeros((int(nvals/2), nfiles_used))
                data[key_col][key_str][:, ifile] = fft_mean_by_col



class SuperbiasFFTConfig(SuperbiasSlotTableAnalysisConfig):
    """Configuration for SuperbiasFFTTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='sbiasfft')
    std = EOUtilOptions.clone_param('std')


class SuperbiasFFTTask(SuperbiasSlotTableAnalysisTask):
    """Analyze the FFT of the superbias frames"""

    ConfigClass = SuperbiasFFTConfig
    _DefaultName = "SuperbiasFFTTask"

    # This is the list of plots, used to make sure that they exist
    plot_names = ['i', 'p', 's', 'i-col', 's-col', 'p-col']

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
            self.log.warn("Ignoring butler.")

        mask_files = self.get_mask_files()
        superbias = self.get_superbias_frame(mask_files)
        if superbias is None:
            return None

        fft_data = {}

        self.log_info_slot_msg(self.config, "")

        freqs_dict = get_readout_freqs_from_ccd(superbias)
        for key in REGION_KEYS:
            freqs = freqs_dict['freqs_%s' % key]
            freqs_col = freqs_dict['freqs_%s_col' % key]
            nfreqs = len(freqs)
            nfreqs_col = len(freqs_col)
            fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])
            fft_data['%s_col' % key] = dict(freqs=freqs_col[0:int(nfreqs_col/2)])

        BiasFFTTask.get_ccd_data(self, superbias, fft_data,
                                 slot=slot, superbias_frame=None)


        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])
            dtables.make_datatable('biasfft-%s_col' % key, fft_data["%s_col" % key])
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
            figs.setup_amp_plots_grid(key, title="FFT of %s region mean by row" % region,
                                      xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]",
                                      ymin=0., ymax=3.)
            figs.plot_xy_amps_from_tabledict(dtables, datakey, key,
                                             x_name='freqs', y_name='fftpow',
                                             ymin=0., ymax=3.)
            datakey_col = "biasfft-%s_col" % key
            figs.setup_amp_plots_grid("%s-col" % key, title="FFT of %s region columns" % region,
                                      xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
            figs.plot_xy_amps_from_tabledict(dtables, datakey_col, "%s-col" % key,
                                             x_name='freqs', y_name='fftpow')


class BiasFFTStatsConfig(BiasRaftTableAnalysisConfig):
    """Configuration for BiasFFTStatsTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='biasfft')
    filekey = EOUtilOptions.clone_param('filekey', default='biasfft-stats')


class BiasFFTStatsTask(BiasRaftTableAnalysisTask):
    """Extract statistics about the FFT of the bias frames"""

    ConfigClass = BiasFFTStatsConfig
    _DefaultName = "BiasFFTStatsTask"

    # This is the list of plots, used to make sure that they exist
    plot_names = ['max-fft', 'max-fft-col']

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
            self.log.warn("Ignoring butler in bias_fft_stats.extract")

        datakey = 'biasfft-s'
        datakey_col = 'biasfft-i_col'

        data_dict = dict(fftpow_mean=[],
                         fftpow_median=[],
                         fftpow_std=[],
                         fftpow_min=[],
                         fftpow_max=[],
                         fftpow_maxval=[],
                         fftpow_argmax=[],
                         fftpow_mean_col=[],
                         fftpow_median_col=[],
                         fftpow_std_col=[],
                         fftpow_min_col=[],
                         fftpow_max_col=[],
                         fftpow_maxval_col=[],
                         fftpow_argmax_col=[],
                         slot=[],
                         amp=[])

        freqs = None

        self.log_info_raft_msg(self.config, "")

        slot_list = self.config.slots
        if slot_list is None:
            slot_list = getSlotList(self.config.raft)

        for islot, slot in enumerate(slot_list):

            basename = data[slot]

            if not os.path.exists(basename):
                self.log.warn("No file %s" % basename)
                continue

            dtables = TableDict(basename, [datakey, datakey_col])
            if not dtables.keys():
                self.log.warn("No tables")
                continue

            self.log_progress("  %s" % slot)
            table = dtables[datakey]
            table_col = dtables[datakey_col]

            if freqs is None:
                freqs = table['freqs']
                freqs_col = table_col['freqs']

            for amp in range(16):
                try:
                    tablevals = table['fftpow_%s_a%02i' % (slot, amp)]
                except KeyError:
                    continue
                tablevals_col = table_col['fftpow_%s_a%02i' % (slot, amp)]
                if len(tablevals.shape) == 1:
                    tablevals = tablevals.reshape(tablevals.shape[0], 1)
                    tablevals_col = tablevals_col.reshape(tablevals_col.shape[0], 1)
                meanvals = np.mean(tablevals, axis=1)
                meanvals_col = np.mean(tablevals_col, axis=1)
                data_dict['fftpow_mean'].append(meanvals)
                data_dict['fftpow_median'].append(np.median(tablevals, axis=1))
                data_dict['fftpow_std'].append(np.std(tablevals, axis=1))
                data_dict['fftpow_min'].append(np.min(tablevals, axis=1))
                data_dict['fftpow_max'].append(np.max(tablevals, axis=1))
                data_dict['fftpow_maxval'].append(meanvals[100:].max())
                data_dict['fftpow_argmax'].append(meanvals[100:].argmax())
                data_dict['fftpow_mean_col'].append(meanvals_col)
                data_dict['fftpow_median_col'].append(np.median(tablevals_col, axis=1))
                data_dict['fftpow_std_col'].append(np.std(tablevals_col, axis=1))
                data_dict['fftpow_min_col'].append(np.min(tablevals_col, axis=1))
                data_dict['fftpow_max_col'].append(np.max(tablevals_col, axis=1))
                data_dict['fftpow_maxval_col'].append(meanvals_col[50:].max())
                data_dict['fftpow_argmax_col'].append(meanvals_col[50:].argmax())
                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        self.log_progress("Done!")

        if not data_dict['amp']:
            return None

        outtables = TableDict()
        if freqs is None:
            freqs = np.zeros((1024), float)
        outtables.make_datatable("freqs", dict(freqs=freqs))
        outtables.make_datatable("freqs_col", dict(freqs=freqs_col))
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
        idxs = sumtable['slot']*16 + sumtable['amp']

        raft_array = np.zeros((144))
        raft_array[idxs] = sumtable['fftpow_maxval']
        figs.plot_stat_color('max-fft', raft_array.reshape(9, 16))

        raft_array = np.zeros((144))
        raft_array[idxs] = sumtable['fftpow_maxval_col']
        figs.plot_stat_color('max-fft-col', raft_array.reshape(9, 16))


        
class BiasFFTRunConfig(BiasRunTableAnalysisConfig):
    """Configuration for BiasFFTRunTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='biasfft-stats')
    filekey = EOUtilOptions.clone_param('filekey', default='biasfft-run')


class BiasFFTRunTask(BiasRunTableAnalysisTask):
    """Summarize the results for the analysis of the FFT of the bias frames"""

    ConfigClass = BiasFFTRunConfig
    _DefaultName = "BiasFFTRunTask"

    plot_names = ['fftpow-maxval', 'fftpow-maxval-col']

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasRunTableAnalysisTask.__init__(self, **kwargs)


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
            output data tables
        """
        self.safe_update(**kwargs)

        for key, val in data.items():
            if isinstance(val, dict):
                try:
                    data[key] = val["S00"].replace(self.config.filekey, self.config.infilekey)
                except KeyError:
                    data[key] = val["SG0"].replace(self.config.filekey, self.config.infilekey)
            else:
                data[key] = val.replace(self.config.filekey, self.config.infilekey)
        # Define the set of columns to keep and remove
        # keep_cols = []
        remove_cols = ['fftpow_mean','fftpow_median','fftpow_std','fftpow_min','fftpow_max','fftpow_argmax','fftpow_mean_col','fftpow_median_col','fftpow_std_col','fftpow_min_col','fftpow_max_col','fftpow_maxval_col','fftpow_argmax_col']

        outtable = vstack_tables(data, tablename='biasfft_stats', remove_cols=remove_cols)

        dtables = TableDict()
        dtables.add_datatable('biasfft_run', outtable)
        dtables.make_datatable('runs', dict(runs=[self.config.run]))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots

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
        table = dtables['biasfft_run']

        figs.plot_amps_data_fp_table('fftpow_maxval',
                                     table, 'fftpow_maxval',
                                     title="Max FFT-Power",
                                     z_range=(0., 2.)) #, ylabel='Gain Ne/DN')
    
    
        
class BiasFFTSummaryConfig(BiasSummaryAnalysisConfig):
    """Configuration for BiasFFTSummaryTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='biasfft-stats')
    filekey = EOUtilOptions.clone_param('filekey', default='biasfft-sum')

class BiasFFTSummaryTask(BiasSummaryAnalysisTask):
    """Summarize the results for the analysis of the FFT of the bias frames"""

    ConfigClass = BiasFFTSummaryConfig
    _DefaultName = "BiasFFTSummaryTask"

    plot_names = ['fftpow-maxval', 'fftpow-maxval-col']

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
            self.log.warn("Ignoring butler in extract()")

        run_dict = dict(runs=[], rafts=[])
        for key, val in data.items():
            run_dict['runs'].append(key[4:])
            run_dict['rafts'].append(key[0:3])
            data[key] = val.replace(self.config.filekey, self.config.infilekey)

        keep_cols = ['fftpow_maxval', 'fftpow_argmax', 'fftpow_maxval_col', 'fftpow_argmax_col', 'slot', 'amp']

        outtable = vstack_tables(data, tablename='biasfft_stats', keep_cols=keep_cols)

        dtables = TableDict()
        dtables.add_datatable('biasfft_sum', outtable)
        dtables.make_datatable('runs', run_dict)
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

        config_table = get_run_config_table(kwargs.get('config_table', 'seq_list.fits'), 'seq')

        sumtable = dtables['biasfft_sum']
        if self.config.teststand == 'ts8':
            runtable = dtables['runs']
            yvals = sumtable['fftpow_maxval'].flatten().clip(0., 2.)
            runs = runtable['runs']
            figs.plot_run_chart("fftpow-maxval", runs, yvals, ylabel="Maximum FFT Power [ADU]")
        elif self.config.teststand == 'bot':
            rafts = np.unique(sumtable['raft'])
            for raft in rafts:
                mask = sumtable['raft'] == raft
                subtable = sumtable[mask]
                figs.plot_run_chart_by_slot("fftpow-maxval-%s" % raft, subtable,
                                            "fftpow_maxval", #yerrs="std",
                                            ylabel="Maximum FFT Power [ADU]",
                                            ymin=0., ymax=2.,
                                            raft=raft,
                                            config_table=config_table)
                figs.plot_run_chart_by_slot("fftpow-maxval-col-%s" % raft, subtable,
                                            "fftpow_maxval_col", #yerrs="std",
                                            ylabel="Maximum FFT Power [ADU]",
                                            ymin=0., ymax=2.,
                                            raft=raft,
                                            config_table=config_table)


EO_TASK_FACTORY.add_task_class('BiasFFT', BiasFFTTask)
EO_TASK_FACTORY.add_task_class('SuperbiasFFT', SuperbiasFFTTask)
EO_TASK_FACTORY.add_task_class('BiasFFTStats', BiasFFTStatsTask)
EO_TASK_FACTORY.add_task_class('BiasFFTRun', BiasFFTRunTask)
EO_TASK_FACTORY.add_task_class('BiasFFTSummary', BiasFFTSummaryTask)
