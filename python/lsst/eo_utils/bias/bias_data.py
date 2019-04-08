"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_dims_from_ccd,\
    get_ccd_from_id, get_raw_image, get_geom_regions, get_amp_list

from .analysis import BiasAnalysisFunc, BiasAnalysisBySlot

DEFAULT_BIAS_TYPE = 'spline'

class bias_v_row(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['bias', 'rafts']
    analysisClass = BiasAnalysisBySlot

    def __init__(self):
        BiasAnalysisFunc.__init__(self, "biasval", self.extract, self.plot)

    @staticmethod
    def extract(butler, slot_data, **kwargs):


    @staticmethod
    def plot(dtables, figs):



def extract_bias_data_slot(butler, slot_data, **kwargs):
    """Stack the overscan region from all the amps on a sensor
    to look for coherent read noise

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
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

    bias_files = slot_data['BIAS']
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
                continue

        get_biasval_data(butler, ccd, biasval_data,
                         ifile=ifile, nfiles=len(bias_files),
                         slot=slot, bias_type=bias_type)

        #Need to truncate the row array to match the data
        a_row = biasval_data[sorted(biasval_data.keys())[0]]
        biasval_data['row_s'] = xrow_s[0:len(a_row)]

        get_bias_fft_data(butler, ccd, fft_data,
                          ifile=ifile, nfiles=len(bias_files),
                          slot=slot, bias_type=bias_type,
                          std=std, superbias_frame=superbias_frame)

        get_bias_struct_data(butler, ccd, biasstruct_data,
                             ifile=ifile, nfiles=len(bias_files),
                             slot=slot, bias_type=bias_type,
                             std=std, superbias_frame=superbias_frame)

        get_correl_wrt_oscan_data(butler, ccd, ref_frames,
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



def plot_bias_data_slot(dtables, figs):
    """Plot the all the bias data
    @param dtables (TableDict)  The data
    @param figs (FigureDict)    Object to store the figues
    """
    plot_bias_v_row_slot(dtables, figs)
    plot_bias_fft_slot(dtables, figs)
    plot_bias_struct_slot(dtables, figs)
    plot_correl_wrt_oscan_slot(dtables, figs)
    plot_oscan_amp_stack_slot(dtables, figs)


