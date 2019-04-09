"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_dims_from_ccd, get_ccd_from_id,\
    get_raw_image, get_geom_regions, get_amp_list, get_image_frames_2d

from .analysis import BiasAnalysisFunc, BiasAnalysisBySlot

DEFAULT_BIAS_TYPE = 'spline'

class correl_wrt_oscan(BiasAnalysisFunc):
    """Class to analyze correlations between the imaging section
    and the overscan regions in a series of bias frames"""

    argnames = STANDARD_SLOT_ARGS + ['covar', 'superbias']
    analysisClass = BiasAnalysisBySlot

    def __init__(self):
        """C'tor"""
        BiasAnalysisFunc.__init__(self, "biasoscorr", self.extract, self.plot)

    @staticmethod
    def extract(butler, slot_data, **kwargs):
        """Extract the correlations between the imaging section
        and the overscan regions in a series of bias frames

        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs:
            slot (str)           Slot in question, i.e., 'S00'

        @returns (`TableDict`) with the extracted data
        """
        slot = kwargs['slot']

        bias_files = slot_data['BIAS']
        mask_files = get_mask_files(**kwargs)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        ref_frames = {}

        nfiles = len(bias_files)
        s_correl = np.ndarray((16, nfiles-1))
        p_correl = np.ndarray((16, nfiles-1))

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)
            if ifile == 0:
                dims = get_dims_from_ccd(butler, ccd)
                nrow_i = dims['nrow_i']
                ncol_i = dims['ncol_i']
                amps = get_amp_list(butler, ccd)
                for i, amp in enumerate(amps):
                    regions = get_geom_regions(butler, ccd, amp)
                    image = get_raw_image(butler, ccd, amp)
                    ref_frames[i] = get_image_frames_2d(image, regions)
                    continue
            correl_wrt_oscan.get_ccd_data(butler, ccd, ref_frames,
                                          ifile=ifile, s_correl=s_correl, p_correl=p_correl,
                                          nrow_i=nrow_i, ncol_i=ncol_i)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        data = {}
        for i in range(16):
            data['s_correl_a%02i' % i] = s_correl[i]
            data['p_correl_a%02i' % i] = p_correl[i]

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        dtables.make_datatable("correl", data)
        return dtables


    @staticmethod
    def plot(dtables, figs):
        """Plot the bias structure

        @param dtables (`TableDict`)  The data
        @param figs (`FigureDict`)    Object to store the figues
        """
        figs.setup_amp_plots_grid("oscorr-row", title="Correlation: imaging region and serial overscan",
                                  xlabel="Correlation",
                                  ylabel="Number of frames")
        figs.setup_amp_plots_grid("oscorr-col", title="Correlation: imaging region and paralell overscan",
                                  xlabel="Correlation",
                                  ylabel="Number of frames")

        df = dtables.get_table("correl")
        for i in range(16):
            s_correl = df['s_correl_a%02i' % i]
            p_correl = df['p_correl_a%02i' % i]
            figs.get_obj('oscorr-row', 'axs').flat[i].hist(s_correl, bins=100, range=(-1., 1.))
            figs.get_obj('oscorr-col', 'axs').flat[i].hist(p_correl, bins=100, range=(-1., 1.))


    @staticmethod
    def get_ccd_data(butler, ccd, ref_frames, **kwargs):
        """Get the bias values and update the data dictionary

        @param butler (`Butler`)   The data butler
        @param ccd (`MaskedCCD`)   The ccd we are getting data from
        @param ref_frames (dict)   Reference data
        @param kwargs:
          ifile (int)                 The file index
          s_correl (np.array)         Serial overscan correlations
          p_correl (np.array)         Parallel overscan correlations
        """
        ifile = kwargs['ifile']
        s_correl = kwargs['s_correl']
        p_correl = kwargs['p_correl']
        nrow_i = kwargs['nrow_i']
        ncol_i = kwargs['ncol_i']

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):

            regions = get_geom_regions(butler, ccd, amp)
            image = get_raw_image(butler, ccd, amp)
            frames = get_image_frames_2d(image, regions)

            ref_i_array = ref_frames[i]['imaging']
            ref_s_array = ref_frames[i]['serial_overscan']
            ref_p_array = ref_frames[i]['parallel_overscan']

            del_i_array = frames['imaging'] - ref_i_array
            del_s_array = frames['serial_overscan'] - ref_s_array
            del_p_array = frames['parallel_overscan'] - ref_p_array

            dd_s = del_s_array.mean(1)[0:nrow_i]-del_i_array.mean(1)
            dd_p = del_p_array.mean(0)[0:ncol_i]-del_i_array.mean(0)
            mask_s = np.fabs(dd_s) < 50.
            mask_p = np.fabs(dd_p) < 50.

            s_correl[i, ifile-1] = np.corrcoef(del_s_array.mean(1)[0:nrow_i][mask_s],
                                               dd_s[mask_s])[0, 1]
            p_correl[i, ifile-1] = np.corrcoef(del_p_array.mean(0)[0:ncol_i][mask_p],
                                               dd_p[mask_p])[0, 1]
