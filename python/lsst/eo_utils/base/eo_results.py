"""Classes to collect EO testing results"""

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.base.file_utils import TS8_EORESULTSIN_FORMATTER,\
    EORESULTS_TABLE_FORMATTER, EORESULTS_PLOT_FORMATTER,\
    EORESULTS_SUMMARY_TABLE_FORMATTER, EORESULTS_SUMMARY_PLOT_FORMATTER

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, SummaryAnalysisIterator




class EOResultsRaftConfig(AnalysisConfig):
    """Configuration for EOResultsRaftTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    insuffix = EOUtilOptions.clone_param('insuffix', default='_eotest_results')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='_eotest_results')


class EOResultsRaftTask(AnalysisTask):
    """Collect results from the production eotest suite"""

    ConfigClass = EOResultsRaftConfig
    _DefaultName = "EOResultsRaftTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = TS8_EORESULTSIN_FORMATTER
    tablename_format = EORESULTS_TABLE_FORMATTER
    plotname_format = EORESULTS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)


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

        slots = ALL_SLOTS

        # This is a dictionary of dictionaries to store all the
        # data you extract from the base_files
        data_dict = dict(slot=np.ndarray((144)))

        for islot, slot in enumerate(slots):
            infile = data[slot]
            dtables = TableDict(infile, ['amplifier_results'])
            table = dtables['amplifier_results']
            data_dict['slot'][16*islot:16*(islot+1)] = islot
            for key in table.keys():
                if key not in data_dict:
                    data_dict[key] = np.ndarray((144))
                data_dict[key][16*islot:16*(islot+1)] = table[key]

        dtables = TableDict()
        dtables.make_datatable('eo_results', data_dict)
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
        table = dtables['eo_results']

        figs.plot_raft_amp_values('gain',
                                  table['GAIN'],
                                  title="Fe55 Gain",
                                  yerrs=table['GAIN_ERROR'],
                                  ylabel='Gain Ne/DN',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('ptc_gain',
                                  table['PTC_GAIN'],
                                  title="PTC Gain",
                                  yerrs=table['PTC_GAIN_ERROR'],
                                  ylabel='Gain Ne/DN',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('read_noise',
                                  table['READ_NOISE'],
                                  title="Read Noise",
                                  ylabel='rms e-/pixel',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('full_well',
                                  table['FULL_WELL'],
                                  title='Full well Measurment',
                                  ylabel='e-/pixel',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('dark_current',
                                  table['DARK_CURRENT_95'],
                                  title='Dark Current 95%',
                                  ylabel='e-/s/pixel',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('cti_high_serial',
                                  table['CTI_HIGH_SERIAL'],
                                  title="CTI High Serial",
                                  yerrs=table['CTI_HIGH_SERIAL_ERROR'],
                                  ylabel='loss/pixel',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('cti_high_parallel',
                                  table['CTI_HIGH_PARALLEL'],
                                  title="CTI High Parallel",
                                  yerrs=table['CTI_HIGH_PARALLEL_ERROR'],
                                  ylabel='loss/pixel',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('cti_low_serial',
                                  table['CTI_LOW_SERIAL'],
                                  title="CTI Low Serial",
                                  yerrs=table['CTI_LOW_SERIAL_ERROR'],
                                  ylabel='loss/pixel',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('cti_low_parallel',
                                  table['CTI_LOW_PARALLEL'],
                                  title="CTI Low Parallel",
                                  yerrs=table['CTI_LOW_PARALLEL_ERROR'],
                                  ylabel='loss/pixel',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('max_frac_dev',
                                  table['MAX_FRAC_DEV'],
                                  title="Maximum fractional deviation",
                                  ylabel='Fraction',
                                  slots=ALL_SLOTS)
        figs.plot_raft_amp_values('psf_sigma',
                                  table['PSF_SIGMA'],
                                  title="PSF Width",
                                  ylabel='pixels',
                                  slots=ALL_SLOTS)


class EOResultsSummaryConfig(AnalysisConfig):
    """Configuration for EOResultsTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    dataset = EOUtilOptions.clone_param('dataset')
    insuffix = EOUtilOptions.clone_param('insuffix', default='_eotest_results')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='_eotest_results_sum')


class EOResultsSummaryTask(AnalysisTask):
    """Summarize the analysis results for many runs"""

    ConfigClass = EOResultsSummaryConfig
    _DefaultName = "EOResultsSummaryTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = EORESULTS_TABLE_FORMATTER
    tablename_format = EORESULTS_SUMMARY_TABLE_FORMATTER
    plotname_format = EORESULTS_SUMMARY_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)

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
            Output data tables
        """
        self.safe_update(**kwargs)

        for key, val in data.items():
            data[key] = val.replace(self.config.outsuffix, self.config.insuffix)

        # Define the set of columns to keep and remove
        # keep_cols = []
        # remove_cols = []

        outtable = vstack_tables(data, tablename='eo_results')

        dtables = TableDict()
        dtables.add_datatable('eo_results_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data

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

        table = dtables['eo_results_sum']
        runtable = dtables['runs']
        runs = runtable['runs']

        figs.plot_run_chart('gain',
                            runs,
                            table['GAIN'],
                            yerrs=table['GAIN_ERROR'],
                            ylabel='Gain Ne/DN')
        figs.plot_run_chart('ptc_gain',
                            runs,
                            table['PTC_GAIN'],
                            yerrs=table['PTC_GAIN_ERROR'],
                            ylabel='Gain Ne/DN')
        figs.plot_run_chart('read_noise',
                            runs,
                            table['READ_NOISE'],
                            ylabel='rms e-/pixel')
        figs.plot_run_chart('shot_noise',
                            runs,
                            table['DC95_SHOT_NOISE'],
                            ylabel='rms e-/pixel')
        figs.plot_run_chart('total_noise',
                            runs,
                            table['TOTAL_NOISE'],
                            ylabel='rms e-/pixel')
        figs.plot_run_chart('full_well',
                            runs,
                            table['FULL_WELL'],
                            ylabel='e-/pixel')
        figs.plot_run_chart('dark_current',
                            runs,
                            table['DARK_CURRENT_95'],
                            ylabel='e-/s/pixel')
        figs.plot_run_chart('cti_high_serial',
                            runs,
                            table['CTI_HIGH_SERIAL'],
                            yerrs=table['CTI_HIGH_SERIAL_ERROR'],
                            ylabel='loss/pixel')
        figs.plot_run_chart('cti_high_parallel',
                            runs,
                            table['CTI_HIGH_PARALLEL'],
                            yerrs=table['CTI_HIGH_PARALLEL_ERROR'],
                            ylabel='loss/pixel')
        figs.plot_run_chart('cti_low_serial',
                            runs,
                            table['CTI_LOW_SERIAL'],
                            yerrs=table['CTI_LOW_SERIAL_ERROR'],
                            ylabel='loss/pixel')
        figs.plot_run_chart('cti_low_parallel',
                            runs,
                            table['CTI_LOW_PARALLEL'],
                            yerrs=table['CTI_LOW_PARALLEL_ERROR'],
                            ylabel='loss/pixel')
        figs.plot_run_chart('max_frac_dev',
                            runs,
                            table['MAX_FRAC_DEV'],
                            ylabel='Fraction')
        figs.plot_run_chart('psf_sigma',
                            runs,
                            table['PSF_SIGMA'],
                            ylabel='pixels')

EO_TASK_FACTORY.add_task_class('EOResultsRaft', EOResultsRaftTask)
EO_TASK_FACTORY.add_task_class('EOResultsSummary', EOResultsSummaryTask)
