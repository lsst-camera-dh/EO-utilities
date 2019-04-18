

import numpy as np

from lsst.eotest.sensor import Fe55GainFitter

from .analysis import Fe55AnalysisFunc

from .meta_analysis import Fe55TableAnalysisByRaft


class fe55_gain_stats(Fe55AnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS
    iteratorClass = Fe55TableAnalysisByRaft
    tablename_func = raft_fe55_tablename
    plotname_func = raft_f355_plotname

    def __init__(self):
        """C'tor """
        Fe55AnalysisFunc.__init__(self, "fe55_gain_stats")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Extract the bias as function of row

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs

        @returns (TableDict) with the extracted data
        """
        if butler is not None:
            sys.stdout.write("Ignoring butler in fe55_gain_stats.extract\n")

        data_dict = dict(kalpha_peak=[],
                         kalpha_sigma=[],
                         ncluster=[],
                         ngood=[],
                         gain=[],
                         gain_error=[],
                         sigmax_mean=[],
                         sigmay_mean=[],
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
                mask = (np.fabs(table['XPOS'] - table['XPEAK']) < 1)*\
                    (np.fabs(table['YPOS'] - table['YPEAK']) < 1)
                tablevals = table[mask]['DN']
                gf = Fe55GainFitter(tablevals)
                kalpha_peak, kalpha_sigma = gf.fit()
                data_dict['kalpha_peak'].append(kalpha_peak)
                data_dict['kalpha_sigma'].append(kalpha_sigma)
                data_dict['ncluster'].append(mask.size)
                data_dict['ngood'].append(mask.sum())
                data_dict['gain'].append(gf.gain)
                data_dict['gain_error'].append(gf.gain_error)
                data_dict['sigmax_mean'].append(np.mean(table[mask]['SIGMAX']))
                data_dict['sigmay_mean'].append(np.mean(table[mask]['SIGMAY']))
                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("fe55_gain_stats", data_dict)
        return outtables


    @staticmethod
    def plot(dtables, figs):
        """Plot the summary data from the bias fft statistics study

        @param dtables (TableDict)    The data we are ploting
        @param fgs (FigureDict)       Keeps track of the figures
        """
        sumtable = dtables['fe55_gain_stats']
        figs.plot_stat_color('gain_array', sumtable['gain'].reshape(9,16))



fe55_gain_stats.run()
