"""Class to analyze the FFT of the bias frames"""

import sys

import lsst.eotest.image_utils as imutils

from lsst.eotest.sensor import EPERTask

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import TableAnalysisByRaft, TableAnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.sflat.file_utils import SUPERFLAT_FORMATTER,\
    SLOT_SFLAT_TABLE_FORMATTER, SLOT_SFLAT_PLOT_FORMATTER,\
    RAFT_SFLAT_TABLE_FORMATTER, RAFT_SFLAT_PLOT_FORMATTER

from lsst.eo_utils.sflat.analysis import SflatAnalysisConfig, SflatAnalysisTask


class CTEConfig(SflatAnalysisConfig):
    """Configuration for CTETask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='cte')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    overscans = EOUtilOptions.clone_param('overscans')
    nframes = EOUtilOptions.clone_param('nframes')

class CTETask(SflatAnalysisTask):
    """Analyze some sflat data"""

    ConfigClass = CTEConfig
    _DefaultName = "CTETask"
    iteratorClass = TableAnalysisBySlot

    intablename_format = SUPERFLAT_FORMATTER
    tablename_format = SLOT_SFLAT_TABLE_FORMATTER
    plotname_format = SLOT_SFLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SflatAnalysisTask.__init__(self, **kwargs)

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

        slot = self.config.slot

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        superflat_file = data[0]
        superflat_lo_file = superflat_file.replace('.fits.fits', '_l.fits')
        superflat_hi_file = superflat_file.replace('.fits.fits', '_h.fits')

        sys.stdout.write("Working on %s" % (slot))
        sys.stdout.flush()

        # This is a dictionary of dictionaries to store all the
        # data you extract from the sflat_files
        data_dict = dict(CTI_LOW_SERIAL=[],
                         CTI_LOW_SERIAL_ERROR=[],
                         CTI_HIGH_SERIAL=[],
                         CTI_HIGH_SERIAL_ERROR=[],
                         CTI_LOW_PARALLEL=[],
                         CTI_LOW_PARALLEL_ERROR=[],
                         CTI_HIGH_PARALLEL=[],
                         CTI_HIGH_PARALLEL_ERROR=[])

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        all_amps = imutils.allAmps(superflat_lo_file)
        gains = None
        nframes = self.config.nframes

        s_task = EPERTask()
        s_task.config.direction = 's'
        s_task.config.verbose = True
        s_task.config.cti = True
        scti_l, bias_ests = s_task.run(superflat_lo_file, nframes, all_amps,
                                       self.config.overscans, gains=gains,
                                       mask_files=mask_files)
        scti_h, bias_ests = s_task.run(superflat_hi_file, nframes, all_amps,
                                       self.config.overscans, gains=gains,
                                       mask_files=mask_files)
        
        #
        # Compute parallel CTE.
        #
        p_task = EPERTask()
        p_task.config.direction = 'p'
        p_task.config.verbose = True
        p_task.config.cti = True
        pcti_l, bias_ests = p_task.run(superflat_lo_file, nframes, all_amps,
                                       self.config.overscans, gains=gains,
                                       mask_files=mask_files)
        pcti_h, bias_ests = p_task.run(superflat_hi_file, nframes, all_amps,
                                       self.config.overscans, gains=gains,
                                       mask_files=mask_files)
        #
        for amp in all_amps:
            data_dict['CTI_LOW_SERIAL'].append(scti_l[amp].value)
            data_dict['CTI_LOW_SERIAL_ERROR'].append(scti_l[amp].error)
            data_dict['CTI_HIGH_SERIAL'].append(scti_h[amp].value)
            data_dict['CTI_HIGH_SERIAL_ERROR'].append(scti_h[amp].error)
            data_dict['CTI_LOW_PARALLEL'].append(pcti_l[amp].value)
            data_dict['CTI_LOW_PARALLEL_ERROR'].append(pcti_l[amp].error)
            data_dict['CTI_HIGH_PARALLEL'].append(pcti_h[amp].value)
            data_dict['CTI_HIGH_PARALLEL_ERROR'].append(pcti_h[amp].error)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        dtables.make_datatable('cte', data_dict)

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

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


class CTEStatsConfig(SflatAnalysisConfig):
    """Configuration for TempalteStatsTask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='cte')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='cte_stats')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')



class CTEStatsTask(SflatAnalysisTask):
    """Extract summary statistics from the data"""

    ConfigClass = CTEStatsConfig
    _DefaultName = "CTEStatsTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SLOT_SFLAT_TABLE_FORMATTER
    tablename_format = RAFT_SFLAT_TABLE_FORMATTER
    plotname_format = RAFT_SFLAT_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SflatAnalysisTask.__init__(self, **kwargs)


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
        outtables.make_datatable("cte", data_dict)
        return outtables


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

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs


EO_TASK_FACTORY.add_task_class('CTE', CTETask)
EO_TASK_FACTORY.add_task_class('CTEStats', CTEStatsTask)
