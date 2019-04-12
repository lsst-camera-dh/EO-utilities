"""Class to analyze the overscan bias as a function of row number"""

import itertools

import numpy as np

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, unbias_amp

from .file_utils import get_superbias_frame

from .analysis import BiasAnalysisFunc, BiasAnalysisByRaft


class oscan_correl(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['mask', 'bias', 'superbias', 'std']
    analysisClass = BiasAnalysisByRaft

    def __init__(self):
        BiasAnalysisFunc.__init__(self, "oscorr")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Extract the correlations between the serial overscan for each amp on a raft

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the bias and mask files
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            run_num (str)        Run number, i.e,. '6106D'
            covar (bool)         Plot covariance instead of correlation
            db (str)             Which database to use
            outdir (str)         Output directory
        """
        covar = kwargs.get('covar', False)
        slots = ALL_SLOTS
        overscans = []
        boundry = 10

        for slot in slots:
            bias_files = data[slot]['BIAS']

            mask_files = get_mask_files(slot=slot, **kwargs)
            superbias_frame = get_superbias_frame(mask_files=mask_files, slot=slot, **kwargs)

            ccd = get_ccd_from_id(butler, bias_files[0], [])
            overscans += oscan_correl.get_ccd_data(butler, ccd, boundry=boundry,
                                                   superbias_frame=superbias_frame)

        namps = len(overscans)
        if covar:
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


    @staticmethod
    def plot(dtables, figs):
        """Plot the bias fft

        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
        """
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
            im = get_raw_image(butler, ccd, amp)
            image = unbias_amp(im, serial_oscan, bias_type=None, superbias_im=superbias_im)
            serial_oscan.grow(-boundry)
            oscan_data = image[serial_oscan]
            step_x = regions['step_x']
            step_y = regions['step_y']
            overscans.append(oscan_data.getArray()[::step_x, ::step_y])
        return overscans
