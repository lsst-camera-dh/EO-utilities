"""Functions to analyse bias and superbias frames"""

import sys
import itertools

import numpy as np

import lsst.afw.math as afwMath
import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.file_utils import makedir_safe,\
    get_mask_files

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.config_utils import DEFAULT_OUTDIR,\
    DEFAULT_STAT_TYPE, DEFAULT_BITPIX

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.image_utils import REGION_KEYS,\
    get_dims_from_ccd, get_readout_frequencies_from_ccd,\
    get_geom_regions, get_dimension_arrays_from_ccd,\
    get_raw_image, get_ccd_from_id, get_amp_list,\
    get_image_frames_2d, make_superbias, flip_data_in_place

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from .file_utils import get_bias_files_run,\
    superbias_filename, superbias_stat_filename,\
    bias_basename, superbias_basename,\
    raft_basename, get_superbias_frame

from .plot_utils import plot_superbias,\
    plot_bias_v_row_slot, plot_bias_fft_slot,\
    plot_correl_wrt_oscan_slot, plot_oscan_amp_stack_slot,\
    plot_bias_struct_slot, plot_oscan_correl_raft

from .data_utils import get_biasval_data, get_bias_fft_data,\
    get_bias_struct_data, get_correl_wrt_oscan_data, stack_by_amps,\
    get_serial_oscan_data

from .butler_utils import get_bias_files_butler


DEFAULT_BIAS_TYPE = 'spline'
SBIAS_TEMPLATE = 'superbias/templates/sbias_template.fits'
ALL_SLOTS = 'S00 S01 S02 S10 S11 S12 S20 S21 S22'.split()


def get_bias_data(butler, run_num, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param: butler (Bulter)  The data Butler
    @param run_num (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    kwargs.pop('run_num', None)
    if butler is None:
        retval = get_bias_files_run(run_num, **kwargs)
    else:
        retval = get_bias_files_butler(butler, run_num, **kwargs)

    return retval


class BiasAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis task over all the slots in a raft"""
    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        super(BiasAnalysisBySlot, self).__init__(analysis_func, get_bias_data, argnames)


class BiasAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over all the raft and then all the slots in a raft"""
    def __init__(self, analysis_func, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        super(BiasAnalysisByRaft, self).__init__(analysis_func, get_bias_data, argnames)



def extract_bias_v_row_slot(butler, slot_data, **kwargs):
    """Extract the bias as function of row

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing

    @returns (TableDict) with the extracted data
    """
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)

    bias_files = slot_data['BIAS']

    sys.stdout.write("Working on %s, %i files: \n" % (slot, len(bias_files)))

    biasval_data = {}

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, [])
        if ifile == 0:
            dims = get_dims_from_ccd(butler, ccd)
            xrow_s = np.linspace(0, dims['nrow_s']-1, dims['nrow_s'])

        get_biasval_data(butler, ccd, biasval_data,
                         ifile=ifile, nfiles=len(bias_files),
                         slot=slot, bias_type=bias_type)

        #Need to truncate the row array to match the data
        a_row = biasval_data[sorted(biasval_data.keys())[0]]
        biasval_data['row_s'] = xrow_s[0:len(a_row)]

    sys.stdout.write("!\n")
    sys.stdout.flush()

    dtables = TableDict()
    dtables.make_datatable('files', make_file_dict(butler, bias_files))
    dtables.make_datatable('biasval', biasval_data)
    return dtables


def extract_bias_fft_slot(butler, slot_data, **kwargs):
    """Extract the FFTs of the row-wise and col-wise struture
    in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        std (bool)           Plot standard deviation instead of median

    @returns (TableDict) with the extracted data
    """
    slot = kwargs['slot']
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)

    bias_files = slot_data['BIAS']
    mask_files = get_mask_files(**kwargs)
    superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    fft_data = {}

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)
        if ifile == 0:
            freqs_dict = get_readout_frequencies_from_ccd(butler, ccd)
            for key in REGION_KEYS:
                freqs = freqs_dict['freqs_%s' % key]
                nfreqs = len(freqs)
                fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])

        get_bias_fft_data(butler, ccd, fft_data,
                          ifile=ifile, nfiles=len(bias_files),
                          slot=slot, bias_type=bias_type,
                          std=std, superbias_frame=superbias_frame)

    sys.stdout.write("!\n")
    sys.stdout.flush()

    dtables = TableDict()
    dtables.make_datatable('files', make_file_dict(butler, bias_files))
    for key in REGION_KEYS:
        dtables.make_datatable('biasfft-%s' % key, fft_data[key])

    return dtables


def extract_bias_struct_slot(butler, slot_data, **kwargs):
    """Plot the row-wise and col-wise struture
    in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        std (bool)           Plot standard deviation instead of median
    """
    slot = kwargs['slot']
    std = kwargs.get('std', False)
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)

    bias_files = slot_data['BIAS']
    mask_files = get_mask_files(**kwargs)
    superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    biasstruct_data = {}

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)
        if ifile == 0:
            dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)
            for key, val in dim_array_dict.items():
                biasstruct_data[key] = {key:val}

        get_bias_struct_data(butler, ccd, biasstruct_data,
                             ifile=ifile, nfiles=len(bias_files),
                             slot=slot, bias_type=bias_type,
                             std=std, superbias_frame=superbias_frame)


    sys.stdout.write("!\n")
    sys.stdout.flush()

    dtables = TableDict()
    dtables.make_datatable('files', make_file_dict(butler, bias_files))
    for key, val in biasstruct_data.items():
        dtables.make_datatable('biasst-%s' % key, val)
    return dtables


def extract_correl_wrt_oscan_slot(butler, slot_data, **kwargs):
    """Extract the correlations between the imaging section
    and the overscan regions in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        slot (str)           Slot in question, i.e., 'S00'

    @returns (TableDict) with the extracted data
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
        get_correl_wrt_oscan_data(butler, ccd, ref_frames,
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


def convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles):
    """Convert the stack arrays to a dictionary

    @param stack_arrays (dict)   The stacked data
    @param dim_array_dict (dict) The array shapes
    @param nfiles (int)          Number of input files

    @returns (dict) the re-organized data
    """
    stackdata_dict = {}

    for key, xvals in dim_array_dict.items():
        stack = stack_arrays[key]
        amp_mean = stack.mean(0).mean(1)
        stackdata_dict[key] = {key:xvals}

        for i in range(nfiles):
            amp_stack = (stack[i].T - amp_mean).T
            mean_val = amp_stack.mean(0)
            std_val = amp_stack.std(0)
            signif_val = mean_val / std_val
            for stat, val in zip(['mean', 'std', 'signif'], [mean_val, std_val, signif_val]):
                keystr = "stack_%s" % stat
                if keystr not in stackdata_dict[key]:
                    stackdata_dict[key][keystr] = np.ndarray((len(val), nfiles))
                stackdata_dict[key][keystr][:, i] = val
    return stackdata_dict



def extract_oscan_amp_stack_slot(butler, slot_data, **kwargs):
    """Stack the overscan region from all the amps on a sensor
    to look for coherent read noise

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
    """
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)

    bias_files = slot_data['BIAS']
    mask_files = get_mask_files(**kwargs)
    superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

    sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
    sys.stdout.flush()

    stack_arrays = {}

    nfiles = len(bias_files)

    for ifile, bias_file in enumerate(bias_files):
        if ifile % 10 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        ccd = get_ccd_from_id(butler, bias_file, mask_files)

        if ifile == 0:
            dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)

            for key, val in dim_array_dict.items():
                stack_arrays[key] = np.zeros((nfiles, 16, len(val)))

        stack_by_amps(stack_arrays, butler, ccd,
                      ifile=ifile, bias_type=bias_type,
                      superbias_frame=superbias_frame)

    sys.stdout.write("!\n")
    sys.stdout.flush()

    stackdata_dict = convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles)

    dtables = TableDict()
    dtables.make_datatable('files', make_file_dict(butler, bias_files))
    for key, val in stackdata_dict.items():
        dtables.make_datatable('stack-%s' % key, val)
    return dtables


def extract_oscan_correl_raft(butler, raft_data, **kwargs):
    """Extract the correlations between the serial overscan for each amp on a raft

    @param butler (Butler)   The data butler
    @param raft_data (dict)  Dictionary pointing to the bias and mask files
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
        bias_files = raft_data[slot]['BIAS']
        ccd = get_ccd_from_id(butler, bias_files[0], [])
        overscans += get_serial_oscan_data(butler, ccd, boundry=boundry)

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


def extract_superbias_fft_slot(butler, slot_data, **kwargs):
    """Extract the FFTs of the row-wise and col-wise struture
    in a superbias frame

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    slot = kwargs['slot']
    std = kwargs.get('std', False)

    if butler is not None:
        sys.stdout.write("Ignoring butler in plot_superbias_fft_slot")

    bias_files = slot_data['BIAS']
    mask_files = get_mask_files(**kwargs)
    superbias = get_superbias_frame(mask_files=mask_files, **kwargs)

    fft_data = {}

    freqs_dict = get_readout_frequencies_from_ccd(None, superbias)
    for key in REGION_KEYS:
        freqs = freqs_dict['freqs_%s' % key]
        nfreqs = len(freqs)
        fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])

    get_bias_fft_data(None, superbias, fft_data,
                      slot=slot, bias_type=kwargs.get('superbias'),
                      std=std, superbias_frame=None)

    sys.stdout.write("!\n")
    sys.stdout.flush()

    dtables = TableDict()
    dtables.make_datatable('files', make_file_dict(butler, bias_files))
    for key in REGION_KEYS:
        dtables.make_datatable('biasfft-%s' % key, fft_data[key])
    return dtables


def extract_superbias_struct_slot(butler, slot_data, **kwargs):
    """Extract the row-wise and col-wise struture  in a superbias frame

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    slot = kwargs['slot']
    std = kwargs.get('std', False)

    if butler is not None:
        sys.stdout.write("Ignoring butler in plot_superbias_fft_slot")

    bias_files = slot_data['BIAS']
    mask_files = get_mask_files(**kwargs)
    superbias = get_superbias_frame(mask_files=mask_files, **kwargs)

    biasstruct_data = {}

    dim_array_dict = get_dimension_arrays_from_ccd(None, superbias)
    for key, val in dim_array_dict.items():
        biasstruct_data[key] = {key:val}

    get_bias_struct_data(None, superbias, biasstruct_data,
                         slot=slot, bias_type=kwargs.get('superbias'),
                         std=std, superbias_frame=None)

    sys.stdout.write("!\n")
    sys.stdout.flush()

    dtables = TableDict()
    dtables.make_datatable('files', make_file_dict(butler, bias_files))
    for key, val in biasstruct_data.items():
        dtables.make_datatable('biasst-%s' % key, val)
    return dtables


def make_superbias_slot(butler, slot_data, **kwargs):
    """Make superbias frame for one slot

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        stat (str)           Statistic to use to stack data
        outdir (str)         Output directory
        bitpix (int)         Output data format BITPIX field
        skip (bool)          Flag to skip making superbias, only produce plots
        plot (bool)          Plot superbias images
        stats_hist (bool)    Plot superbias summary histograms
    """
    raft = kwargs['raft']
    run_num = kwargs['run_num']
    slot = kwargs['slot']
    bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
    outdir = kwargs.get('outdir', DEFAULT_OUTDIR)
    stat_type = kwargs.get('stat', DEFAULT_STAT_TYPE)

    bias_files = slot_data['BIAS']
    mask_files = get_mask_files(**kwargs)

    sys.stdout.write("Working on %s, %i files.\n" % (slot, len(bias_files)))

    if stat_type.upper() in afwMath.__dict__:
        statistic = afwMath.__dict__[stat_type.upper()]
    else:
        raise ValueError("Can not convert %s to a valid statistic to perform stacking" % stat_type)

    if statistic == afwMath.MEDIAN:
        output_file = superbias_filename(outdir, raft, run_num, slot, bias_type)
        subtract_mean = True
        vmin = -20.
        vmax = 20.
    else:
        output_file = superbias_stat_filename(outdir, raft, run_num, slot,
                                              stat_type=stat_type, bias_type=bias_type)
        subtract_mean = False

    makedir_safe(output_file)

    if not kwargs.get('skip', False):
        sbias = make_superbias(butler, bias_files,
                               statistic=statistic,
                               bias_type=bias_type)
        imutil.writeFits(sbias, output_file, SBIAS_TEMPLATE, kwargs.get('bitpix', DEFAULT_BITPIX))
        if butler is not None:
            flip_data_in_place(output_file)

    if subtract_mean:
        plot_superbias(output_file, mask_files,
                       subtract_mean=True, vmin=vmin, vmax=vmax,
                       **kwargs)
    else:
        plot_superbias(output_file, mask_files, **kwargs)


class BiasAnalysisFunc:
    """Simple functor class to tie together standard bias data analysis
    """
    def __init__(self, outbase_func, datasuffix, extract_func, plot_func):
        """ C'tor

        @param outbase_func (func)  Function to get output path
        @param datasuffix (func)    Suffix for data file
        @param extract_func (func)  Function to extract data
        @param plot_func (func)     Function to plot data
        """
        self.outbase_func = outbase_func
        self.datasuffix = datasuffix
        self.extract_func = extract_func
        self.plot_func = plot_func

    def __call__(self, butler, slot_data, **kwargs):
        """Tie together the functions
        @param butler (Butler)   The data butler
        @param slot_data (dict)  Dictionary pointing to the bias and mask files
        @param kwargs
        """
        outbase = self.outbase_func(**kwargs)
        makedir_safe(outbase)
        output_data = outbase + "_data_%s.fits" % self.datasuffix

        if kwargs.get('skip', False):
            dtables = TableDict(output_data)
        else:
            dtables = self.extract_func(butler, slot_data, **kwargs)
            dtables.save_datatables(output_data)

        if kwargs.get('plot', False):
            self.plot_func(dtables, outbase)


def make_bias_v_row_slot(butler, slot_data, **kwargs):
    """Extract the bias as function of row

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        outdir (str)         Output directory
        plot (bool)          Make plots
    """
    ba = BiasAnalysisFunc(bias_basename, "biasval",
                          extract_bias_v_row_slot, plot_bias_v_row_slot)
    ba(butler, slot_data, **kwargs)


def make_bias_fft_slot(butler, slot_data, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    ba = BiasAnalysisFunc(bias_basename, "biasfft",
                          extract_bias_fft_slot, plot_bias_fft_slot)
    ba(butler, slot_data, **kwargs)



def make_bias_struct_slot(butler, slot_data, **kwargs):
    """Plot the row-wise and col-wise struture
    in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    ba = BiasAnalysisFunc(bias_basename, "biasst",
                          extract_bias_struct_slot, plot_bias_struct_slot)
    ba(butler, slot_data, **kwargs)


def make_correl_wrt_oscan_slot(butler, slot_data, **kwargs):
    """Plot the correlations between the imaging section
    and the overscan regions in a series of bias frames

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        outdir (str)         Output directory
    """
    ba = BiasAnalysisFunc(bias_basename, "biasoscorr",
                          extract_correl_wrt_oscan_slot, plot_correl_wrt_oscan_slot)
    ba(butler, slot_data, **kwargs)



def make_oscan_amp_stack_slot(butler, slot_data, **kwargs):
    """Stack the overscan region from all the amps on a sensor
    to look for coherent read noise

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
    """
    ba = BiasAnalysisFunc(bias_basename, "biasosstack",
                          extract_oscan_amp_stack_slot, plot_oscan_amp_stack_slot)
    ba(butler, slot_data, **kwargs)


def make_oscan_correl_raft(butler, raft_data, **kwargs):
    """Extract the correlations between the serial overscan for each amp on a raft

    @param butler (Butler)   The data butler
    @param raft_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        covar (bool)         Plot covariance instead of correlation
        db (str)             Which database to use
        outdir (str)         Output directory
    """
    if kwargs.get('covar', False):
        suffix = "oscov"
    else:
        suffix = "oscorr"
    ba = BiasAnalysisFunc(raft_basename, suffix,
                          extract_oscan_correl_raft, plot_oscan_correl_raft)
    ba(butler, raft_data, **kwargs)


def make_superbias_fft_slot(butler, slot_data, **kwargs):
    """Plot the FFTs of the row-wise and col-wise struture
    in a superbias frame

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    ba = BiasAnalysisFunc(superbias_basename, "sbiasfft",
                          extract_superbias_fft_slot, plot_bias_fft_slot)
    ba(butler, slot_data, **kwargs)


def make_superbias_struct_slot(butler, slot_data, **kwargs):
    """Plot the row-wise and col-wise struture  in a superbias frame

    @param butler (Butler)   The data butler
    @param slot_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        slot (str)           Slot in question, i.e., 'S00'
        superbias (str)      Method to use for superbias subtraction
        outdir (str)         Output directory
        std (bool)           Plot standard deviation instead of median
    """
    ba = BiasAnalysisFunc(superbias_basename, "sbiasst",
                          extract_superbias_struct_slot, plot_bias_struct_slot)
    ba(butler, slot_data, **kwargs)
