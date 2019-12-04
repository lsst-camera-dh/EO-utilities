"""Class to analyze the FFT of the bias frames"""

import numpy as np

from lsst.eotest.sensor import Traps

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.ppump.analysis import PpumpAnalysisConfig, PpumpAnalysisTask


class TrapConfig(PpumpAnalysisConfig):
    """Configuration for TrapTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='trap')
    cycles = EOUtilOptions.clone_param('cycles')
    threshold = EOUtilOptions.clone_param('threshold')
    C2_thresh = EOUtilOptions.clone_param('C2_thresh')
    C3_thresh = EOUtilOptions.clone_param('C3_thresh')
    bkg_nx = EOUtilOptions.clone_param('bkg_nx')
    bkg_ny = EOUtilOptions.clone_param('bkg_ny')
    edge_rolloff = EOUtilOptions.clone_param('edge_rolloff')


class TrapTask(PpumpAnalysisTask):
    """Analyze some pocket-pumped data to find traps"""

    ConfigClass = TrapConfig
    _DefaultName = "TrapTask"
    iteratorClass = AnalysisBySlot

    plot_names = []

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

        gains = np.ones((17))

        ppump_files = data['PPUMP']
        print(ppump_files)
        ppump_file = ppump_files[0]

        mask_files = self.get_mask_files()

        self.log_info_slot_msg(self.config, "")

        # This is a dictionary of dictionaries to store all the
        # data you extract from the ppump_files
        data_dict = {}

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        ccd = self.get_ccd(butler, ppump_file, mask_files, masked_ccd=True)

        my_traps = Traps(ccd, gains, cycles=self.config.cycles,
                         C2_thresh=self.config.C2_thresh,
                         C3_thresh=self.config.C3_thresh,
                         nx=self.config.bkg_nx, ny=self.config.bkg_ny,
                         edge_rolloff=self.config.edge_rolloff)

        data_dict = my_traps.make_data_dict()

        self.log_progress("Done!")

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, ppump_files))
        dtables.make_datatable('traps', data_dict)

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


EO_TASK_FACTORY.add_task_class('Trap', TrapTask)
