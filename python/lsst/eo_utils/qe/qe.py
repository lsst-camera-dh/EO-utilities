"""Class to analyze the FFT of the bias frames"""

import numpy as np

from lsst.eotest.sensor.QE import QE_Data

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .meta_analysis import QeSlotTableAnalysisConfig, QeSlotTableAnalysisTask


class QEConfig(QeSlotTableAnalysisConfig):
    """Configuration for QETask"""
    insuffix = EOUtilOptions.clone_param('insuffix', default='qe_med')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='qe')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class QETask(QeSlotTableAnalysisTask):
    """Analyze some qe data"""

    ConfigClass = QEConfig
    _DefaultName = "QETask"

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

        self.log_info_slot_msg(self.config, "")

        pd_calib_file = self.get_pd_calib_file()
        gains = np.ones((17))

        basename = data[0]

        qe_data = QE_Data()
        qe_data.read_fits(basename)
        qe_data.incidentPower(pd_calib_file)
        qe_data.calculate_QE(gains)

        qe_curves_data_dict = qe_data.make_qe_curves_data_dict()
        bands_data_dict = qe_data.make_bands_data_dict()

        dtables = TableDict()
        dtables.make_datatable('qe_curves', qe_curves_data_dict)
        dtables.make_datatable('bands', bands_data_dict)

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


EO_TASK_FACTORY.add_task_class('QE', QETask)
