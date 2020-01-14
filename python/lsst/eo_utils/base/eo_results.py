"""Classes to collect EO testing results"""

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, vstack_tables

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.base.file_utils import EORESULTSIN_FORMATTER,\
    EORESULTS_TABLE_FORMATTER, EORESULTS_PLOT_FORMATTER,\
    EORESULTS_RUNTABLE_FORMATTER, EORESULTS_RUNPLOT_FORMATTER,\
    EORESULTS_SUMMARY_TABLE_FORMATTER, EORESULTS_SUMMARY_PLOT_FORMATTER

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, TableAnalysisByRun, SummaryAnalysisIterator




class EOResultsRaftConfig(AnalysisConfig):
    """Configuration for EOResultsRaftTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    teststand = EOUtilOptions.clone_param('teststand')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    calib = EOUtilOptions.clone_param('calib', default='eotest')
    infilekey = EOUtilOptions.clone_param('infilekey', default='results')
    filekey = EOUtilOptions.clone_param('filekey', default='results')


class EOResultsRaftTask(AnalysisTask):
    """Collect results from the production eotest suite"""

    ConfigClass = EOResultsRaftConfig
    _DefaultName = "EOResultsRaftTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = EORESULTSIN_FORMATTER
    tablename_format = EORESULTS_TABLE_FORMATTER
    plotname_format = EORESULTS_PLOT_FORMATTER

    datatype = 'eotest'

    # This is the list of plots, used to make sure that they exist
    plot_names = ['gain', 'ptc-gain', 'read-noise', 'full-well',
                  'dark-current', 'cti-high-serial', 'cti-high-parallel',
                  'cti-low-serial', 'cti-low-parallel', 'max-frac-dev',
                  'psf-sigma']

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
            try:
                dtables = TableDict(infile, ['amplifier_results'])
            except FileNotFoundError:
                return None
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

        try:
            figs.plot_raft_amp_values('gain',
                                      table['GAIN'],
                                      title="Fe55 Gain",
                                      yerrs=table['GAIN_ERROR'],
                                      ylabel='Gain Ne/DN',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('ptc-gain',
                                      table['PTC_GAIN'],
                                      title="PTC Gain",
                                      yerrs=table['PTC_GAIN_ERROR'],
                                      ylabel='Gain Ne/DN',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('read-noise',
                                      table['READ_NOISE'],
                                      title="Read Noise",
                                      ylabel='rms e-/pixel',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('full-well',
                                      table['FULL_WELL'],
                                      title='Full well Measurment',
                                      ylabel='e-/pixel',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('dark-current',
                                      table['DARK_CURRENT_95'],
                                      title='Dark Current 95%',
                                      ylabel='e-/s/pixel',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('cti-high-serial',
                                      table['CTI_HIGH_SERIAL'],
                                      title="CTI High Serial",
                                      yerrs=table['CTI_HIGH_SERIAL_ERROR'],
                                      ylabel='loss/pixel',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('cti-high-parallel',
                                      table['CTI_HIGH_PARALLEL'],
                                      title="CTI High Parallel",
                                      yerrs=table['CTI_HIGH_PARALLEL_ERROR'],
                                      ylabel='loss/pixel',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('cti-low-serial',
                                      table['CTI_LOW_SERIAL'],
                                      title="CTI Low Serial",
                                      yerrs=table['CTI_LOW_SERIAL_ERROR'],
                                      ylabel='loss/pixel',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('cti-low-parallel',
                                      table['CTI_LOW_PARALLEL'],
                                      title="CTI Low Parallel",
                                      yerrs=table['CTI_LOW_PARALLEL_ERROR'],
                                      ylabel='loss/pixel',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('max-frac-dev',
                                      table['MAX_FRAC_DEV'],
                                      title="Maximum fractional deviation",
                                      ylabel='Fraction',
                                      slots=ALL_SLOTS)
            figs.plot_raft_amp_values('psf-sigma',
                                      table['PSF_SIGMA'],
                                      title="PSF Width",
                                      ylabel='pixels',
                                      slots=ALL_SLOTS)
        except KeyError:
            pass





class EOResultsRunConfig(AnalysisConfig):
    """Configuration for EOResultsRaftTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    teststand = EOUtilOptions.clone_param('teststand')
    run = EOUtilOptions.clone_param('run')
    calib = EOUtilOptions.clone_param('calib', default='eotest')
    infilekey = EOUtilOptions.clone_param('infilekey', default='results')
    filekey = EOUtilOptions.clone_param('filekey', default='results')


class EOResultsRunTask(AnalysisTask):
    """Collect results from the production eotest suite"""

    ConfigClass = EOResultsRunConfig
    _DefaultName = "EOResultsRunTask"
    iteratorClass = TableAnalysisByRun

    intablename_format = EORESULTS_TABLE_FORMATTER
    tablename_format = EORESULTS_RUNTABLE_FORMATTER
    plotname_format = EORESULTS_RUNPLOT_FORMATTER

    datatype = 'eotest'

    # This is the list of plots, used to make sure that they exist
    plot_names = ['gain', 'ptc-gain', 'read-noise', 'full-well',
                  'dark-current', 'cti-high-serial', 'cti-high-parallel',
                  'cti-low-serial', 'cti-low-parallel', 'max-frac-dev',
                  'psf-sigma']

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

        for key, val in data.items():
            print(key, val)
            data[key] = val.replace(self.config.filekey, self.config.infilekey)

        # Define the set of columns to keep and remove
        # keep_cols = []
        # remove_cols = []

        outtable = vstack_tables(data, tablename='eo_results')

        dtables = TableDict()
        dtables.add_datatable('eo_results_run', outtable)
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
        table = dtables['eo_results_run']

        try:
            figs.plot_amps_data_fp_table('gain',
                                         table, 'GAIN',
                                         title="Fe55 Gain",
                                         z_range=(0., 2.)) #, ylabel='Gain Ne/DN')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('ptc-gain',
                                         table, 'PTC_GAIN',
                                         title="PTC Gain",
                                         z_range=(0., 2.)) #, ylabel='Gain Ne/DN')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('read-noise',
                                         table, 'READ_NOISE',
                                         title="Read Noise",
                                         z_range=(0., 20.)) #, ylabel='rms e-/pixel')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('full-well',
                                         table, 'FULL_WELL',
                                         title='Full well Measurment',
                                         z_range=(0., 3e5))# , ylabel='e-/pixel')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('dark-current',
                                         table, 'DARK_CURRENT_95',
                                         title='Dark Current 95%',
                                         z_range=(1e-3, 1.), use_log10=True) #,ylabel='e-/s/pixel')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('cti-high-serial',
                                         table, 'CTI_HIGH_SERIAL',
                                         title="CTI High Serial",
                                         z_range=(-1e-5, 1e-5)) # ,ylabel='loss/pixel')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('cti-high-parallel',
                                         table, 'CTI_HIGH_PARALLEL',
                                         title="CTI High Parallel",
                                         z_range=(-1e-5, 1e-5)) # ,ylabel='loss/pixel')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('cti-low-serial',
                                         table, 'CTI_LOW_SERIAL',
                                         title="CTI Low Serial",
                                         z_range=(-1e-5, 1e-5)) # ,ylabel='loss/pixel')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('cti-low-parallel',
                                         table, 'CTI_LOW_PARALLEL',
                                         title="CTI Low Parallel",
                                         z_range=(-1e-5, 1e-5)) #, ylabel='loss/pixel')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('max-frac-dev',
                                         table, 'MAX_FRAC_DEV',
                                         title="Maximum fractional deviation",
                                         z_range=(1e-5, 1e-1), use_log10=True) #, ylabel='Fraction')
        except KeyError:
            pass

        try:
            figs.plot_amps_data_fp_table('psf-sigma',
                                         table, 'PSF_SIGMA',
                                         title="PSF Width",
                                         z_range=(0, 4.)) #, ylabel='pixels')
        except KeyError:
            pass





class EOResultsSummaryConfig(AnalysisConfig):
    """Configuration for EOResultsTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    teststand = EOUtilOptions.clone_param('teststand')
    dataset = EOUtilOptions.clone_param('dataset')
    calib = EOUtilOptions.clone_param('calib', default='eotest')
    infilekey = EOUtilOptions.clone_param('infilekey', default='results')
    filekey = EOUtilOptions.clone_param('filekey', default='results_sum')


class EOResultsSummaryTask(AnalysisTask):
    """Summarize the analysis results for many runs"""

    ConfigClass = EOResultsSummaryConfig
    _DefaultName = "EOResultsSummaryTask"
    iteratorClass = SummaryAnalysisIterator

    intablename_format = EORESULTS_TABLE_FORMATTER
    tablename_format = EORESULTS_SUMMARY_TABLE_FORMATTER
    plotname_format = EORESULTS_SUMMARY_PLOT_FORMATTER

    # This is the list of plots, used to make sure that they exist
    plot_names = ['gain', 'ptc-gain', 'read-noise', 'full-well',
                  'dark-current', 'cti-high-serial', 'cti-high-parallel',
                  'cti-low-serial', 'cti-low-parallel', 'max-frac-dev',
                  'psf-sigma']

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
            data[key] = val.replace(self.config.filekey, self.config.infilekey)

        # Define the set of columns to keep and remove
        # keep_cols = []
        # remove_cols = []

        outtable = vstack_tables(data, tablename='eo_results')

        dtables = TableDict()
        dtables.add_datatable('eo_results_sum', outtable)
        dtables.make_datatable('runs', dict(runs=sorted(data.keys())))
        return dtables


    def plot_ts8(self, dtables, figs, **kwargs):
        """Plot the summary data for ts8 runs

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

        try:
            figs.plot_run_chart('gain',
                                runs,
                                table['GAIN'],
                                yerrs=table['GAIN_ERROR'],
                                ylabel='Gain Ne/DN',
                                ymin=0, ymax=2.)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('ptc-gain',
                                runs,
                                table['PTC_GAIN'],
                                yerrs=table['PTC_GAIN_ERROR'],
                                ylabel='Gain Ne/DN',
                                ymin=0, ymax=2.)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('read-noise',
                                runs,
                                table['READ_NOISE'],
                                ylabel='rms e-/pixel',
                                ymin=0, ymax=10.)
        except KeyError:
            pass


        try:
            figs.plot_run_chart('shot-noise',
                                runs,
                                table['DC95_SHOT_NOISE'],
                                ylabel='rms e-/pixel',
                                ymin=0, ymax=10.)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('total-noise',
                                runs,
                                table['TOTAL_NOISE'],
                                ylabel='rms e-/pixel',
                                ymin=0, ymax=10.)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('full-well',
                                runs,
                                table['FULL_WELL'],
                                ylabel='e-/pixel',
                                ymin=0, ymax=3.0e+5)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('dark-current',
                                runs,
                                table['DARK_CURRENT_95'],
                                ylabel='e-/s/pixel',
                                ymin=0, ymax=10.)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('cti-high-serial',
                                runs,
                                table['CTI_HIGH_SERIAL'],
                                yerrs=table['CTI_HIGH_SERIAL_ERROR'],
                                ylabel='loss/pixel',
                                ymin=0, ymax=1.0e-4)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('cti-high-parallel',
                                runs,
                                table['CTI_HIGH_PARALLEL'],
                                yerrs=table['CTI_HIGH_PARALLEL_ERROR'],
                                ylabel='loss/pixel',
                                ymin=0, ymax=1.0e-4)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('cti-low-serial',
                                runs,
                                table['CTI_LOW_SERIAL'],
                                yerrs=table['CTI_LOW_SERIAL_ERROR'],
                                ylabel='loss/pixel',
                                ymin=0, ymax=1.0e-4)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('cti-low-parallel',
                                runs,
                                table['CTI_LOW_PARALLEL'],
                                yerrs=table['CTI_LOW_PARALLEL_ERROR'],
                                ylabel='loss/pixel',
                                ymin=0, ymax=1.0e-4)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('max-frac-dev',
                                runs,
                                table['MAX_FRAC_DEV'],
                                ylabel='Fraction',
                                ymin=0, ymax=1.0e-2)
        except KeyError:
            pass

        try:
            figs.plot_run_chart('psf-sigma',
                                runs,
                                table['PSF_SIGMA'],
                                ylabel='pixels',
                                ymin=0., ymax=4.)
        except KeyError:
            pass



    def plot_by_raft(self, raft, raft_table, figs, **kwargs):
        """Plot the summary data

        Parameters
        ----------
        raft : `str`
            The raft name
        raft_table : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)
        figs.plot_run_chart_by_slot('gain-%s' % raft,
                                    raft_table, 'GAIN',
                                    yerrs='GAIN_ERROR',
                                    ylabel='Gain Ne/DN',
                                    ymin=0, ymax=2.)
        figs.plot_run_chart_by_slot('ptc-gain-%s' % raft,
                                    raft_table, 'PTC_GAIN',
                                    yerrs='PTC_GAIN_ERROR',
                                    ylabel='Gain Ne/DN',
                                    ymin=0, ymax=2.)
        figs.plot_run_chart_by_slot('read-noise-%s' % raft,
                                    raft_table, 'READ_NOISE',
                                    ylabel='rms e-/pixel',
                                    ymin=0, ymax=20.)
        figs.plot_run_chart_by_slot('shot-noise-%s' % raft,
                                    raft_table, 'DC95_SHOT_NOISE',
                                    ylabel='rms e-/pixel',
                                    ymin=0, ymax=20.)
        figs.plot_run_chart_by_slot('total-noise-%s' % raft,
                                    raft_table, 'TOTAL_NOISE',
                                    ylabel='rms e-/pixel',
                                    ymin=0, ymax=20.)
        figs.plot_run_chart_by_slot('full-well-%s' % raft,
                                    raft_table, 'FULL_WELL',
                                    ylabel='e-/pixel',
                                    ymin=0, ymax=3.0e+5)
        figs.plot_run_chart_by_slot('dark-current-%s' % raft,
                                    raft_table, 'DARK_CURRENT_95',
                                    ylabel='e-/s/pixel',
                                    logy=True,
                                    ymin=1e-3, ymax=1.)
        figs.plot_run_chart_by_slot('cti-high-serial-%s' % raft,
                                    raft_table, 'CTI_HIGH_SERIAL',
                                    yerrs='CTI_HIGH_SERIAL_ERROR',
                                    ylabel='loss/pixel',
                                    ymin=-1e-5, ymax=1e-5)
        figs.plot_run_chart_by_slot('cti-high-parallel-%s' % raft,
                                    raft_table, 'CTI_HIGH_PARALLEL',
                                    yerrs='CTI_HIGH_PARALLEL_ERROR',
                                    ylabel='loss/pixel',
                                    ymin=-1e-5, ymax=1e-5)
        figs.plot_run_chart_by_slot('cti-low-serial-%s' % raft,
                                    raft_table, 'CTI_LOW_SERIAL',
                                    yerrs='CTI_LOW_SERIAL_ERROR',
                                    ylabel='loss/pixel',
                                    ymin=-1e-5, ymax=1e-5)
        figs.plot_run_chart_by_slot('cti-low-parallel-%s' % raft,
                                    raft_table, 'CTI_LOW_PARALLEL',
                                    yerrs='CTI_LOW_PARALLEL_ERROR',
                                    ylabel='loss/pixel',
                                    ymin=-1e-5, ymax=1e-5)
        figs.plot_run_chart_by_slot('max-frac-dev-%s' % raft,
                                    raft_table, 'MAX_FRAC_DEV',
                                    ylabel='Fraction',
                                    logy=True,
                                    ymin=1e-5, ymax=1e-1)
        figs.plot_run_chart_by_slot('psf-sigma-%s' % raft,
                                    raft_table, 'PSF_SIGMA',
                                    ylabel='pixels',
                                    ymin=0., ymax=4.)



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

        if self.config.teststand == 'ts8':
            self.plot_ts8(dtables, figs, **kwargs)
        elif self.config.teststand == 'bot':
            sumtable = dtables['eo_results_sum']
            rafts = np.unique(sumtable['raft'])
            for raft in rafts:
                mask = sumtable['raft'] == raft
                subtable = sumtable[mask]
                self.plot_by_raft(raft, subtable, figs, **kwargs)


EO_TASK_FACTORY.add_task_class('EOResultsRaft', EOResultsRaftTask)
EO_TASK_FACTORY.add_task_class('EOResultsRun', EOResultsRunTask)
EO_TASK_FACTORY.add_task_class('EOResultsSummary', EOResultsSummaryTask)
