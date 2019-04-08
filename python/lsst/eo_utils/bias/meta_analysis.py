"""Functions to analyse summary data from bias and superbias frames"""

import sys
import numpy as np

from lsst.eo_utils.base.file_utils import read_runlist, makedir_safe
from lsst.eo_utils.base.data_utils import TableDict, vstack_tables
from lsst.eo_utils.base.plot_utils import FigureDict
from lsst.eo_utils.bias.file_utils import slot_bias_tablename,\
    raft_bias_tablename, raft_superbias_tablename,\
    bias_summary_tablename, bias_summary_plotname,\
    superbias_summary_tablename, superbias_summary_plotname

from .analysis import BiasAnalysisFunc

SLOT_LIST = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']


def extract_fft_stats_run(run_num, raft, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param rum_num (str)     The run number
    @param raft (str)        The raft id
    @param kwargs:
        bias (str)
        superbias (str)
    """

    datakey = 'biasfft-s'
    bias_type = kwargs.get('bias')
    superbias_type = kwargs.get('superbias')

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

    sys.stdout.write("Working on %s:")
    sys.stdout.flush()
    for islot, slot in enumerate(SLOT_LIST):

        sys.stdout.write(" %s" % slot)
        sys.stdout.flush()

        basename = slot_bias_tablename('analysis', raft, run_num, slot,
                                       bias=bias_type, superbias=superbias_type, suffix='biasfft')
        datapath = basename + '.fits'

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
    outtables.make_datatable("biasfft_sum", data_dict)
    return outtables


def extract_fft_stats_runlist(infile, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param infile
    @param kwargs:
        bias (str)
        superbias (str)
    """
    run_list = read_runlist(infile)
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]

        outtables = extract_fft_stats_run(run_num, raft, **kwargs)
        outfile = raft_bias_tablename('analysis', raft, run_num,
                                      suffix='biasfft_sum', **kwargs)
        outfile += ".fits"
        outtables.save_datatables(outfile)



def get_raft_bias_tablefiles(infile, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param infile
    @param kwargs:
        bias (str)
        superbias (str)
        """
    run_list = read_runlist(infile)

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]
        run_key = "%s_%s" % (raft, run_num)
        filedict[run_key] = raft_bias_tablename('analysis', raft, run_num, **kwargs) + '.fits'

    return filedict


def get_raft_superbias_tablefiles(infile, **kwargs):
    """Extract the statistics of the FFT of the bias

    @param infile
    @param kwargs:
        bias (str)
        superbias (str)
        """
    run_list = read_runlist(infile)

    filedict = {}
    for runinfo in run_list:
        raft = runinfo[0].replace('-Dev', '')
        run_num = runinfo[1]
        run_key = "%s_%s" % (raft, run_num)
        filedict[run_key] = raft_superbias_tablename('analysis', raft, run_num, **kwargs) + '.fits'

    return filedict



class BiasSummaryAnalysisFunc(BiasAnalysisFunc):
    """Simple functor class to tie together standard bias data analysis
    """
    def __init__(self, datasuffix="", extract_func=None, plot_func=None, **kwargs):
        """ C'tor
        @param datasuffix (func)        Suffix for filenames
        @param extract_func (func)      Function to extract table data
        @param plot_func (func)         Function to make plots
        @param kwargs:
           tablename_func (func)     Function to get output path for tables
           plotname_func (func)      Function to get output path for plots
        """
        kwargs.setdefault('tablename_func', bias_summary_tablename)
        kwargs.setdefault('plotname_func', bias_summary_plotname)
        BiasAnalysisFunc.__init__(self, datasuffix, extract_func, plot_func, **kwargs)


    def make_datatables(self, dataset, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (Butler)   The data butler
        @param slot_data (dict)  Dictionary pointing to the bias and mask files
        @param kwargs

        @return (TableDict)
        """
        tablebase = self.tablename_func(dataset=dataset, suffix=self.datasuffix, **kwargs)
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if kwargs.get('skip', False):
            dtables = TableDict(output_data)
        else:
            dtables = self.extract_func(dataset, **kwargs)
            dtables.save_datatables(output_data)
        return dtables

    def make_plots(self, dtables):
        """Tie together the functions to make the data tables
        @param dtables (TableDict)   The data tables

        @return (FigureDict)
        """
        figs = FigureDict()
        self.plot_func(dtables, figs)
        return figs

    def __call__(self, dataset, **kwargs):
        """Tie together the functions
        @param butler (Butler)   The data butler
        @param slot_data (dict)  Dictionary pointing to the bias and mask files
        @param kwargs
        """
        dtables = self.make_datatables(dataset, **kwargs)
        if kwargs.get('plot', False):
            figs = self.make_plots(dtables)
            if kwargs.get('interactive', False):
                figs.save_all(None)
            else:
                plotbase = self.plotname_func(dataset=dataset, **kwargs)
                makedir_safe(plotbase)
                figs.save_all(plotbase)





def extract_summary_table_bias_fft(dataset, **kwargs):
    """Make a summry table of the bias FFT data

    @param dataset (str)      The name of the dataset
    @param kwargs
        bias (str)
        superbias (str)

    @returns (TableDict)
    """
    infile = '%s_runs.txt' % dataset
    keep_cols = ['fftpow_maxval', 'fftpow_argmax', 'slot', 'amp']

    filedict = get_raft_bias_tablefiles(infile, suffix='biasfft_sum', **kwargs)
    outtable = vstack_tables(filedict, tablename='biasfft_sum', keep_cols=keep_cols)

    dtables = TableDict()
    dtables.add_datatable('biasfft_sum', outtable)
    dtables.make_datatable('runs', dict(runs=sorted(filedict.keys())))
    return dtables


def extract_summary_table_superbias_stats(dataset, **kwargs):
    """Make a summry table of the bias FFT data

    @param dataset (str)      The name of the dataset
    @param kwargs
        bias (str)
        superbias (str)

    @returns (TableDict)
    """
    infile = '%s_runs.txt' % dataset

    filedict = get_raft_superbias_tablefiles(infile,
                                             suffix='stats'
                                             **kwargs)
    outtable = vstack_tables(filedict, tablename='stats')

    dtables = TableDict()
    dtables.add_datatable('stats', outtable)
    dtables.make_datatable('runs', dict(runs=sorted(filedict.keys())))
    return dtables



def plot_summary_table_bias_fft(dtables, figs):
    """Plot the summary data from the bias FFT study

    @param dtables (TableDict)    The data we are ploting
    @param fgs (FigureDict)       Keeps track of the figures
    """
    sumtable = dtables['biasfft_sum']
    runtable = dtables['runs']

    yvals = sumtable['fftpow_maxval'].flatten().clip(0., 2.)
    runs = runtable['runs']

    figs.plot_run_chart("fftpow_maxval", runs, yvals, ylabel="Maximum FFT Power [ADU]")


def plot_summary_table_superbias_stats(dtables, figs):
    """Plot the summary data from the superbias statistics study

    @param dtables (TableDict)    The data we are ploting
    @param fgs (FigureDict)       Keeps track of the figures
    """
    sumtable = dtables['stats']
    runtable = dtables['runs']
    yvals = sumtable['mean'].flatten().clip(0., 30.)
    yerrs = sumtable['std'].flatten().clip(0., 10.)
    runs = runtable['runs']

    figs.plot_run_chart("stats", runs, yvals, yerrs=yerrs, ylabel="Superbias STD [ADU]")


def make_summary_table_bias_fft(dataset, **kwargs):
    """Make a summry table of the bias FFT data

    @param dataset (str)      The name of the dataset
    @param kwargs
        bias (str)
        superbias (str)

    @returns (TableDict)
    """
    functor = BiasSummaryAnalysisFunc('biasfft_sum',
                                      extract_summary_table_bias_fft,
                                      plot_summary_table_bias_fft)
    functor.run(dataset, **kwargs)


def make_summary_table_superbias_stats(dataset, **kwargs):
    """Make a summry table of the bias FFT data

    @param dataset (str)      The name of the dataset
    @param kwargs
        bias (str)
        superbias (str)

    @returns (TableDict)
    """
    functor = BiasSummaryAnalysisFunc('biasfft_sum',
                                      extract_summary_table_superbias_stats,
                                      plot_summary_table_superbias_stats,
                                      tablename_func=superbias_summary_tablename,
                                      plotname_func=superbias_summary_plotname)
    functor.run(dataset, **kwargs)
