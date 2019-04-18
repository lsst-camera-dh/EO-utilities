
import sys

import numpy as np

from lsst.eotest.sensor import Fe55GainFitter

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from .file_utils import fe55_summary_tablename, fe55_summary_plotname,\
    raft_fe55_tablename, raft_fe55_plotname

from .analysis import Fe55AnalysisFunc

from .meta_analysis import Fe55SummaryByRaft, Fe55TableAnalysisByRaft,\
    Fe55SummaryAnalysisFunc


class fe55_gain_stats(Fe55AnalysisFunc):
    """Class to analyze the overscan fe55 as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['use_all']
    iteratorClass = Fe55TableAnalysisByRaft
    tablename_func = raft_fe55_tablename
    plotname_func = raft_fe55_plotname

    def __init__(self):
        """C'tor """
        Fe55AnalysisFunc.__init__(self, "_fe55_gain_stats")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Extract the fe55 as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the fe55 and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
        """
        if butler is not None:
            sys.stdout.write("Ignoring butler in fe55_gain_stats.extract\n")

        use_all = kwargs.get('use_all', False)

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

        freqs = None

        sys.stdout.write("Working on 9 slots: " )
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace('.fits', '_fe55-clusters.fits')

            dtables = TableDict(datapath)
           
            for amp in range(16):
                table = dtables['amp%02i' % (amp+1)]
                if use_all: 
                    mask = np.ones((len(table)), bool)
                else:
                    mask = (np.fabs(table['XPOS'] - table['XPEAK']) < 1)*\
                        (np.fabs(table['YPOS'] - table['YPEAK']) < 1)
                tablevals = table[mask]['DN']                    
                gf = Fe55GainFitter(tablevals)
                try:
                    kalpha_peak, kalpha_sigma = gf.fit(bins=100)
                    gain = gf.gain
                    gain_error = gf.gain_error
                    pars = gf.pars
                except:
                    kalpha_peak, kalpha_sigma = (np.nan, np.nan) 
                    gain = np.nan
                    gain_error = np.nan
                    pars = np.nan * np.ones((4))
                data_dict['kalpha_peak'].append(kalpha_peak)
                data_dict['kalpha_sigma'].append(kalpha_sigma)
                data_dict['gain'].append(gain)
                data_dict['gain_error'].append(gain_error)
                xr = gf.xrange
                data_dict['ncluster'].append(mask.size)
                data_dict['ngood'].append(mask.sum())
                if xr is None:
                    data_dict['fit_xmin'].append(np.nan)
                    data_dict['fit_xmax'].append(np.nan)
                else:
                    data_dict['fit_xmin'].append(xr[0])
                    data_dict['fit_xmax'].append(xr[1])
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


    @staticmethod
    def plot(dtables, figs):
        """Plot the summary data from the fe55 fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        sumtable = dtables['fe55_gain_stats']
        figs.plot_stat_color('gain_array', sumtable['gain'].reshape(9,16))




class fe55_gain_summary(Fe55SummaryAnalysisFunc):
    """Class to analyze the overscan fe55 as a function of row number"""

    argnames = ['dataset', 'butler_repo', 'skip', 'plot', 'use_all']
    iteratorClass = Fe55SummaryByRaft
    tablename_func = fe55_summary_tablename
    plotname_func = fe55_summary_plotname

    def __init__(self):
        """C'tor"""
        Fe55SummaryAnalysisFunc.__init__(self, "_fe55_gain_sum")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Make a summry table of the fe55 FFT data

        @param filedict (dict)      The files we are analyzing
        @param kwargs

        @returns (TableDict)
        """
        if butler is not None:
            sys.stdout.write("Ignoring butler in fe55_gain_summary.extract\n")

        if kwargs.get('use_all', False):
            insuffix = '_all_fe55_gain_stats.fits'
        else:
            insuffix = '_good_fe55_gain_stats.fits'
        for key,val in data.items():
            data[key] = val.replace('.fits', insuffix)

        KEEP_COLS = ['kalpha_peak', 'kalpha_sigma', 'ncluster', 'ngood',
                     'gain', 'gain_error',
                     'sigmax_median', 'sigmay_median',
                     'slot', 'amp']

        if not kwargs.get('skip', False):
            outtable = vstack_tables(data, tablename='fe55_gain_stats',
                                     keep_cols=KEEP_COLS)

        dtables = TableDict()
        dtables.add_datatable('fe55_gain_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    @staticmethod
    def plot(dtables, figs):
        """Plot the summary data from the superfe55 statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
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
