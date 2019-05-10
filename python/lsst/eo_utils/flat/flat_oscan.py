"""Class to analyze the FFT of the bias frames"""

import sys

import numpy as np

from lsst.eotest.sensor.overscan_fit import OverscanFit

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_ccd_from_id

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig, FlatAnalysisTask


class FlatOverscanConfig(FlatAnalysisConfig):
    """Configuration for FlatFlatOverscanTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='flat_oscan')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    num_oscan_pixels = EOUtilOptions.clone_param('num_oscan_pixels')
    minflux = EOUtilOptions.clone_param('minflux')
    maxflux = EOUtilOptions.clone_param('maxflux')


class FlatOverscanTask(FlatAnalysisTask):
    """Estimate the deffered charge by analyzing the overscan in flat frames"""

    ConfigClass = FlatOverscanConfig
    _DefaultName = "FlatOverscanTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        FlatAnalysisTask.__init__(self, **kwargs)
        self.maxflux = 150000.
        self.xmax = 512

    def extract(self, butler, data, **kwargs):
        """Extract the data from the overscan region
        to estimate the deffered charge

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
            raise ValueError("FlatOverscanTask not implemented for Butlerized data")

        slot = self.config.slot

        flat_files = data['FLAT1']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(flat_files)))
        sys.stdout.flush()

        fitter = OverscanFit(num_oscan_pixels=self.config.num_oscan_pixels,
                             minflux=self.config.minflux, maxflux=self.config.maxflux)

        # FIXME
        gains = np.ones((17))

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis

        for ifile, flat_id in enumerate(flat_files):

            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            flat = get_ccd_from_id(butler, flat_id, mask_files, bias_frame=superbias_frame)
            fitter.process_image(flat, gains)

        self.xmax = fitter.xmax_val
        sys.stdout.write("!\n")
        sys.stdout.flush()

        data_dict = fitter.build_output_dict()

        primary = fitter.output[0]
        primary.header['NAMPS'] = 16

        dtables = TableDict(primary=primary)
        for key, val in data_dict.items():
            dtables.make_datatable(key, val)
        dtables.make_datatable('files', make_file_dict(butler, flat_files))

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots of the overscan data to study 
        the deffered charge

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

        self.epr_plot(dtables, figs)
        self.overscan1_plot(dtables, figs)
        self.overscan2_plot(dtables, figs)
        self.summedoverscan_plot(dtables, figs)
        self.cti_plot(dtables, figs)
        self.noise_plot(dtables, figs)


    def epr_plot(self, dtables, figs):
        """Plot the data showing the signal levels 

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        """
        figs.setup_amp_plots_grid('eper', title='Mean Overscans',
                                  xlabel="Overscan Pixel Number", ylabel="Signal [e-]",
                                  ymin=-2, ymax=300.)

        target_flux_levels = [100, 1000, 10000, 25000, 50000, 75000, 100000]

        for i, amp in enumerate(range(1, 17)):

            target_flux_index = 0
            data = dtables['amp{0:02d}'.format(amp)]

            sorted_indices = np.argsort(data['FLUX'])

            axs = figs.get_amp_axes('eper', i)

            for row in sorted_indices:

                flux = data['FLUX'][row]

                if flux <= target_flux_levels[target_flux_index]:
                    continue

                meanrow = data['MEANROW'][row, :]
                offset = np.mean(meanrow[-20:])
                overscan = meanrow[self.xmax:] - offset
                columns = np.arange(self.xmax, meanrow.shape[0])

                axs.plot(columns, overscan, label='{0:d} e-'.format(int(round(flux, -2))))
                axs.set_yscale('symlog', linthreshy=1.0)
                axs.set_yticklabels([r'$-1$', '0', '1', r'$10^{1}$', r'$10^{2}$'])
                axs.grid(True, which='major', axis='both')
                axs.tick_params(axis='both', which='minor')

                leg_h, leg_l = axs.get_legend_handles_labels()

                target_flux_index += 1
                if target_flux_index == len(target_flux_levels):
                    break

        fig = figs.get_figure('eper')

        fig.subplots_adjust(bottom=0.13)
        fig.legend(leg_h, leg_l, loc='lower center', ncol=len(target_flux_levels))


    def overscan1_plot(self, dtables, figs):
        """Plot the data showing the signal in the first overscan pixel

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        """
        f_dict = figs.setup_figure('overscan1',
                                   xlabel='Flux [e-]',
                                   ylabel='First Overscan [e-]')

        axs = f_dict['axes']

        for i, amp in enumerate(range(1, 17)):

            if i >= 10:
                marker = 's'
            else:
                marker = '^'

            data = dtables['amp{0:02d}'.format(amp)]

            sorted_indices = np.argsort(data['FLUX'])

            offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)
            overscan1 = data['MEANROW'][sorted_indices, self.xmax] - offset
            flux = data['FLUX'][sorted_indices] - offset

            axs.plot(flux[flux <= self.maxflux], overscan1[flux <= self.maxflux],
                     label="Amp {0}".format(i+1), marker=marker)

        axs.set_ylim(bottom=-1.0)
        axs.set_xlim(left=50)
        axs.set_yscale('symlog', threshold=1.0)
        axs.set_xscale('log')
        axs.grid(True, which='major', axis='both')

        leg_h, leg_l = axs.get_legend_handles_labels()
        axs.legend(leg_h, leg_l, loc='upper left', ncol=4, fontsize=12)


    def overscan2_plot(self, dtables, figs):
        """Plot the data showing the signal in the second overscan pixel

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        """
        f_dict = figs.setup_figure('overscan2',
                                   xlabel='Flux [e-]',
                                   ylabel='Second Overscan [e-]')

        axs = f_dict['axes']
        axs.grid(True, which='major', axis='both')

        for i, amp in enumerate(range(1, 17)):

            if i >= 10:
                marker = 's'
            else:
                marker = '^'

            data = dtables['amp{0:02d}'.format(amp)]

            sorted_indices = np.argsort(data['FLUX'])

            offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)
            overscan2 = data['MEANROW'][sorted_indices, self.xmax+1] - offset
            flux = data['FLUX'][sorted_indices] - offset

            axs.plot(flux[flux <= self.maxflux], overscan2[flux <= self.maxflux],
                     label="Amp {0}".format(i+1), marker=marker)

        axs.set_yscale('symlog', threshold=1.0)
        axs.set_xscale('log')
        axs.set_ylim(bottom=-1.0)
        axs.set_xlim(left=50)

        leg_h, leg_l = axs.get_legend_handles_labels()
        axs.legend(leg_h, leg_l, loc='upper left', ncol=4, fontsize=12)


    def summedoverscan_plot(self, dtables, figs):
        """Plot the data showing summed signal in the overscan region

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        """
        f_dict = figs.setup_figure('summed',
                                   title='Summed Overscan [8:18]',
                                   xlabel='Flux [e-]',
                                   ylabel='Summed Overscan [e-]')

        axs = f_dict['axes']

        for i, amp in enumerate(range(1, 17)):

            if i >= 10:
                marker = 's'
            else:
                marker = '^'

            data = dtables['amp{0:02d}'.format(amp)]

            sorted_indices = np.argsort(data['FLUX'])

            offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)
            summedoverscan = np.sum(data['MEANROW'][sorted_indices, self.xmax+8:self.xmax+18],
                                    axis=1) - offset
            flux = data['FLUX'][sorted_indices] - offset

            axs.plot(flux[flux <= self.maxflux], summedoverscan[flux <= self.maxflux],
                     label="Amp {0}".format(i+1), marker=marker)

        axs.set_yscale('symlog', threshold=1.0)
        axs.set_xscale('log')
        axs.set_ylim(bottom=-1.0)
        axs.set_xlim(left=50)
        axs.grid(True, which='major', axis='both')
        leg_h, leg_l = axs.get_legend_handles_labels()
        axs.legend(leg_h, leg_l, loc='upper left', ncol=4, fontsize=12)


    def cti_plot(self, dtables, figs):
        """Plot the data showing the charge transfer inefficiency

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        """
        f_dict = figs.setup_figure('cti',
                                   title='CTI from EPER',
                                   xlabel='Flux [e-]',
                                   ylabel='Summed Overscan [e-]')

        axs = f_dict['axes']

        for i, amp in enumerate(range(1, 17)):

            if i >= 10:
                marker = 's'
            else:
                marker = '^'

            data = dtables['amp{0:02d}'.format(amp)]
            sorted_indices = np.argsort(data['FLUX'])

            offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)
            overscan1 = data['MEANROW'][sorted_indices, self.xmax] - offset
            overscan2 = data['MEANROW'][sorted_indices, self.xmax + 1] - offset
            lastpixel = data['MEANROW'][sorted_indices, self.xmax - 1] - offset
            cti = (overscan1 + overscan2)/(self.xmax * lastpixel)
            flux = data['FLUX'][sorted_indices] - offset

            axs.loglog(lastpixel[flux <= self.maxflux], cti[flux <= self.maxflux],
                       label="Amp {0}".format(i+1), marker=marker)

        axs.axhline(y=0.000005, color='black', linestyle='--')
        axs.set_ylim(bottom=5E-8, top=2E-4)
        axs.set_xlim(left=50.0)
        axs.grid(True, which='major', axis='both')

        leg_h, leg_l = axs.get_legend_handles_labels()
        axs.legend(leg_h, leg_l, loc='upper left', ncol=4, fontsize=12)


    def noise_plot(self, dtables, figs):
        """Plot the data showing the overscan noise

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        """
        f_dict = figs.setup_figure('noise',
                                   title='Overscan Noise vs. Flux',
                                   xlabel='Flux [e-]',
                                   ylabel='Overscan Noise [e-]')
        axs = f_dict['axes']

        for i, amp in enumerate(range(1, 17)):

            if i >= 10:
                marker = 's'
            else:
                marker = '^'

            data = dtables['amp{0:02d}'.format(amp)]
            sorted_indices = np.argsort(data['FLUX'])

            noise = data['NOISE'][sorted_indices]
            flux = data['FLUX'][sorted_indices]

            axs.semilogx(flux[flux <= self.maxflux], noise[flux <= self.maxflux],
                         label="Amp {0}".format(i+1), marker=marker)

        axs.set_ylim(0.0, 10.0)
        axs.grid(True, which='major', axis='both')

        leg_h, leg_l = axs.get_legend_handles_labels()
        axs.legend(leg_h, leg_l, loc='lower right', ncol=4, fontsize=12)


class FlatOverscanStatsConfig(FlatAnalysisConfig):
    """Configuration for FlatSlotTempalteStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='flat_oscan')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='flat_oscan_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class FlatOverscanStatsTask(FlatAnalysisTask):
    """Extract statistics about deffered charge from overscan analysis"""

    ConfigClass = FlatOverscanStatsConfig
    _DefaultName = "FlatOverscanStatsTask"
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
        """Extract summary statistics about the serial overscan data

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

        # You should expand this to include space for the data you want to extract
        data_dict = dict(slot=[],
                         amp=[])

        sys.stdout.write("Working on 9 slots: ")
        sys.stdout.flush()

        for islot, slot in enumerate(ALL_SLOTS):

            sys.stdout.write(" %s" % slot)
            sys.stdout.flush()

            basename = data[slot]
            datapath = basename.replace(self.config.outsuffix, self.config.insuffix)

            dtables = TableDict(datapath)

            for amp in range(16):

                # Here you can get the data out for each amp and append it to the
                # data_dict

                data_dict['slot'].append(islot)
                data_dict['amp'].append(amp)

        sys.stdout.write(".\n")
        sys.stdout.flush()

        outtables = TableDict()
        outtables.make_datatable("flat_oscan", data_dict)
        return outtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots from the summer statistics of the serial overscan data

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

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs




EO_TASK_FACTORY.add_task_class('FlatOverscan', FlatOverscanTask)
EO_TASK_FACTORY.add_task_class('FlatOverscanStats', FlatOverscanStatsTask)
