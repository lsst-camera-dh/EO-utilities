"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import REGION_KEYS, get_dims_from_ccd,\
    get_ccd_from_id, get_raw_image, get_geom_regions, get_amp_list,\
    get_dimension_arrays_from_ccd, get_readout_frequencies_from_ccd,\
    get_image_frames_2d

from .data_utils import stack_by_amps, convert_stack_arrays_to_dict

from .file_utils import get_superbias_frame

from .analysis import BiasAnalysisFunc, BiasAnalysisBySlot

from .bias_v_row import bias_v_row

from .bias_fft import bias_fft

from .bias_struct import bias_struct

from .correl_wrt_oscan import correl_wrt_oscan

from .oscan_amp_stack import oscan_amp_stack


# FIXME, this should come from somewhere else
DEFAULT_BIAS_TYPE = 'spline'

class bias_data(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['bias', 'rafts']
    iteratorClass = BiasAnalysisBySlot

    def __init__(self):
        BiasAnalysisFunc.__init__(self, "biasval")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Stack the overscan region from all the amps on a sensor
        to look for coherent read noise

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the bias and mask files
        @param kwargs
            slot (str)           Slot in question, i.e., 'S00'
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            bias (str)           Method to use for unbiasing
            superbias (str)      Type of superbias frame
            std (bool)           Plot standard deviation instead of median
            superbias (str)      Method to use for superbias subtraction
        """
        slot = kwargs['slot']
        bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
        std = kwargs.get('std', False)

        bias_files = data['BIAS']
        mask_files = get_mask_files(**kwargs)
        superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        biasval_data = {}
        fft_data = {}
        biasstruct_data = {}
        stack_arrays = {}
        ref_frames = {}

        nfiles = len(bias_files)
        s_correl = np.ndarray((16, nfiles-1))
        p_correl = np.ndarray((16, nfiles-1))

        nfiles = len(bias_files)
        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)

            if ifile == 0:
                dims = get_dims_from_ccd(butler, ccd)
                dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)
                xrow_s = dim_array_dict['row_s']
                nrow_i = dims['nrow_i']
                ncol_i = dims['ncol_i']
                freqs_dict = get_readout_frequencies_from_ccd(butler, ccd)
                amps = get_amp_list(butler, ccd)
                for key in REGION_KEYS:
                    freqs = freqs_dict['freqs_%s' % key]
                    nfreqs = len(freqs)
                    fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])
                for key, val in dim_array_dict.items():
                    stack_arrays[key] = np.zeros((nfiles, 16, len(val)))
                    biasstruct_data[key] = {key:val}
                for i, amp in enumerate(amps):
                    regions = get_geom_regions(butler, ccd, amp)
                    image = get_raw_image(butler, ccd, amp)
                    ref_frames[i] = get_image_frames_2d(image, regions)

            bias_v_row.get_ccd_data(butler, ccd, biasval_data,
                                    ifile=ifile, nfiles=len(bias_files),
                                    slot=slot, bias_type=bias_type)

            #Need to truncate the row array to match the data
            a_row = biasval_data[sorted(biasval_data.keys())[0]]
            biasval_data['row_s'] = xrow_s[0:len(a_row)]

            bias_fft.get_ccd_data(butler, ccd, fft_data,
                                  ifile=ifile, nfiles=len(bias_files),
                                  slot=slot, bias_type=bias_type,
                                  std=std, superbias_frame=superbias_frame)

            bias_struct.get_ccd_data(butler, ccd, biasstruct_data,
                                     ifile=ifile, nfiles=len(bias_files),
                                     slot=slot, bias_type=bias_type,
                                     std=std, superbias_frame=superbias_frame)

            correl_wrt_oscan.get_ccd_data(butler, ccd, ref_frames,
                                          ifile=ifile, s_correl=s_correl, p_correl=p_correl,
                                          nrow_i=nrow_i, ncol_i=ncol_i)

            stack_by_amps(stack_arrays, butler, ccd,
                          ifile=ifile, bias_type=bias_type,
                          superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        data = {}
        for i in range(16):
            data['s_correl_a%02i' % i] = s_correl[i]
            data['p_correl_a%02i' % i] = p_correl[i]

        stackdata_dict = convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles)

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        dtables.make_datatable('biasval', biasval_data)
        dtables.make_datatable("correl", data)
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])
        for key, val in biasstruct_data.items():
            dtables.make_datatable('biasst-%s' % key, val)
        for key, val in stackdata_dict.items():
            dtables.make_datatable('stack-%s' % key, val)
        return dtables

    @staticmethod
    def plot(dtables, figs):
        """Plot the all the bias data
        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
        """
        bias_v_row.plot(dtables, figs)
        bias_fft.plot(dtables, figs)
        bias_struct.plot(dtables, figs)
        correl_wrt_oscan.plot(dtables, figs)
        oscan_amp_stack.plot(dtables, figs)
