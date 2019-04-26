"""Class to analyze the overscan bias as a function of row number"""

import itertools

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, unbias_amp

from lsst.eo_utils.base.analysis import EO_TASK_FACTORY

from .file_utils import get_superbias_frame,\
    RAFT_BIAS_TABLE_FORMATTER, RAFT_BIAS_PLOT_FORMATTER

from .analysis import BiasAnalysisTask, BiasAnalysisConfig, BiasAnalysisByRaft



class OscanCorrelConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    suffix = EOUtilOptions.clone_param('suffix', default='oscorr')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')
    covar = EOUtilOptions.clone_param('covar')


class OscanCorrelTask(BiasAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = OscanCorrelConfig
    _DefaultName = "OscanCorrelTask"
    iteratorClass = BiasAnalysisByRaft

    tablename_format = RAFT_BIAS_TABLE_FORMATTER
    plotname_format = RAFT_BIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor"""
        BiasAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the bias and mask files
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            run_num (str)        Run number, i.e,. '6106D'
            covar (bool)         Plot covariance instead of correlation
            outdir (str)         Output directory
        """
        self.safe_update(**kwargs)

        slots = ALL_SLOTS
        overscans = []
        boundry = 10

        kwcopy = kwargs.copy()
        for slot in slots:
            bias_files = data[slot]['BIAS']

            kwcopy['slot'] = slot
            mask_files = get_mask_files(self, **kwcopy)
            superbias_frame = get_superbias_frame(self, mask_files=mask_files, **kwcopy)

            ccd = get_ccd_from_id(butler, bias_files[0], [])
            overscans += self.get_ccd_data(butler, ccd, boundry=boundry,
                                           superbias_frame=superbias_frame)

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
        """Plot the bias fft

        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
        """
        self.safe_update(**kwargs)
        data = dtables.get_table('correl')['correl']
        figs.plot_raft_correl_matrix("oscorr", data, title="Overscan Correlations", slots=ALL_SLOTS)


    @staticmethod
    def get_ccd_data(butler, ccd, **kwargs):
        """Get the serial overscan data

        @param butler (Butler)   The data butler
        @param ccd (MaskedCCD)   The ccd we are getting data from
        @param kwargs:
          boundry  (int)              Size of buffer around edge of overscan region
          bias_type (str)             Method to use to construct bias
          superbias_frame (MaskedCCD) The superbias

        @returns (list) the overscan data
        """
        boundry = kwargs.get('boundry', 10)
        amps = get_amp_list(butler, ccd)
        superbias_frame = kwargs.get('superbias_frame', None)
        overscans = []
        for amp in amps:
            if superbias_frame is not None:
                if butler is not None:
                    superbias_im = get_raw_image(None, superbias_frame, amp+1)
                else:
                    superbias_im = get_raw_image(None, superbias_frame, amp)
            else:
                superbias_im = None

            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(butler, ccd, amp)
            image = unbias_amp(img, serial_oscan, bias_type=None, superbias_im=superbias_im)
            serial_oscan.grow(-boundry)
            oscan_data = image[serial_oscan]
            step_x = regions['step_x']
            step_y = regions['step_y']
            overscans.append(oscan_data.getArray()[::step_x, ::step_y])
        return overscans

EO_TASK_FACTORY.add_task_class('OscanCorrel', OscanCorrelTask)
