"""Class to analyze the FFT of the bias frames"""

import lsst.eotest.image_utils as imutils

from lsst.eotest.sensor import EPERTask

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .file_utils import SUPERFLAT_FORMATTER

from .meta_analysis import SflatSlotTableAnalysisConfig,\
    SflatSlotTableAnalysisTask

class CTEConfig(SflatSlotTableAnalysisConfig):
    """Configuration for CTETask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='cte')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    overscans = EOUtilOptions.clone_param('overscans')
    nframes = EOUtilOptions.clone_param('nframes')

class CTETask(SflatSlotTableAnalysisTask):
    """Analyze overscans in superflat data to measure the CTE"""

    ConfigClass = CTEConfig
    _DefaultName = "CTETask"

    intablename_format = SUPERFLAT_FORMATTER

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

        mask_files = self.get_mask_files()
        #superbias_frame = self.get_superbias_frame(mask_files)

        superflat_file = data[0]
        superflat_lo_file = superflat_file.replace('_l.fits', '_l.fits')
        superflat_hi_file = superflat_file.replace('_l.fits', '_h.fits')

        self.log_info_slot_msg(self.config, "")

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
        scti_l, _ = s_task.run(superflat_lo_file, nframes, all_amps,
                               self.config.overscans, gains=gains,
                               mask_files=mask_files)
        scti_h, _ = s_task.run(superflat_hi_file, nframes, all_amps,
                               self.config.overscans, gains=gains,
                               mask_files=mask_files)

        #
        # Compute parallel CTE.
        #
        p_task = EPERTask()
        p_task.config.direction = 'p'
        p_task.config.verbose = True
        p_task.config.cti = True
        pcti_l, _ = p_task.run(superflat_lo_file, nframes, all_amps,
                               self.config.overscans, gains=gains,
                               mask_files=mask_files)
        pcti_h, _ = p_task.run(superflat_hi_file, nframes, all_amps,
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

        self.log_progress("Done!")

        dtables = TableDict()
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


EO_TASK_FACTORY.add_task_class('CTE', CTETask)
