"""Class to analyze the correlations between the overscans for all amplifiers on a raft"""

import copy

import itertools

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, unbias_amp

from lsst.eo_utils.base.iter_utils import AnalysisByRaft

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .file_utils import RAFT_BIAS_TABLE_FORMATTER, RAFT_BIAS_PLOT_FORMATTER

from .analysis import BiasAnalysisTask, BiasAnalysisConfig



class OscanCorrelConfig(BiasAnalysisConfig):
    """Configuration for OscanCorrelTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='oscorr')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')
    covar = EOUtilOptions.clone_param('covar')


class OscanCorrelTask(BiasAnalysisTask):
    """Analyze the correlations between the overscans for all amplifiers on a raft"""

    ConfigClass = OscanCorrelConfig
    _DefaultName = "OscanCorrelTask"
    iteratorClass = AnalysisByRaft

    tablename_format = RAFT_BIAS_TABLE_FORMATTER
    plotname_format = RAFT_BIAS_PLOT_FORMATTER

    boundry = 10

    def extract(self, butler, data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

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

        slots = ALL_SLOTS
        overscans = []

        for slot in slots:
            bias_files = data[slot]['BIAS']

            mask_files = self.get_mask_files(slot=slot)
            superbias_frame = self.get_superbias_frame(mask_files, slot=slot)

            ccd = get_ccd_from_id(butler, bias_files[0], [])
            overscans += self.get_ccd_data(butler, ccd, superbias_frame=superbias_frame)

        namps = len(overscans)

        if self.config.covar:
            data = np.array([np.cov(overscans[i[0]].ravel(),
                                    overscans[i[1]].ravel())[0, 1]
                             for i in itertools.product(range(namps), range(namps))])
        else:
            data = np.array([np.corrcoef(overscans[i[0]].ravel(),
                                         overscans[i[1]].ravel())[0, 1]
                             for i in itertools.product(range(namps), range(namps))])
        data = data.reshape(namps, namps)

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        dtables.make_datatable('correl', dict(correl=data))
        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Plot the correlations between the serial overscan for each amp on a raft

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
        data = dtables.get_table('correl')['correl']
        figs.plot_raft_correl_matrix("oscorr", data, title="Overscan Correlations", slots=ALL_SLOTS)


    def get_ccd_data(self, butler, ccd, **kwargs):
        """Get the serial overscan data

        Parameters
        ----------
        butler : `Butler`
            The data butler
        ccd : `MaskedCCD`
            The ccd we are getting data from
        data : `dict`
            The data we are updating

        Keywords
        --------
        superbias_frame : `MaskedCCD`
            The superbias frame to subtract away
        boundry : `int`
            Size of buffer around edge of overscan region

        Returns
        -------
        overscans : `list`
            The overscan data
        """
        amps = get_amp_list(ccd)
        superbias_frame = kwargs.get('superbias_frame', None)
        overscans = []
        for amp in amps:

            superbias_im = self.get_superbias_amp_image(butler, superbias_frame, amp)
            regions = get_geom_regions(ccd, amp)
            serial_oscan = regions['serial_overscan']

            img = get_raw_image(ccd, amp)
            image = unbias_amp(img, serial_oscan, bias_type=None, superbias_im=superbias_im)
            oscan_copy = copy.deepcopy(serial_oscan)
            oscan_copy.grow(-self.boundry)
            oscan_data = image[oscan_copy]
            step_x = regions['step_x']
            step_y = regions['step_y']
            overscans.append(oscan_data.getArray()[::step_x, ::step_y])
        return overscans

EO_TASK_FACTORY.add_task_class('OscanCorrel', OscanCorrelTask)
