"""Functions to analyse bias and superbias frames"""

import sys

import numpy as np

import lsst.afw.math as afwMath
import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.file_utils import makedir_safe,\
    get_mask_files

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.config_utils import DEFAULT_OUTDIR,\
    DEFAULT_STAT_TYPE, DEFAULT_BITPIX

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.image_utils import REGION_KEYS,\
    get_dims_from_ccd, get_readout_frequencies_from_ccd,\
    get_geom_regions, get_dimension_arrays_from_ccd,\
    get_raw_image, get_ccd_from_id, get_amp_list,\
    get_image_frames_2d, make_superbias, flip_data_in_place

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from .file_utils import get_bias_files_run,\
    superbias_filename, superbias_stat_filename,\
    slot_bias_tablename, slot_bias_plotname,\
    raft_superbias_tablename, raft_superbias_plotname,\
    get_superbias_frame

from .plot_utils import plot_superbias

from .data_utils import stack_by_amps,\
    get_superbias_stats, convert_stack_arrays_to_dict

from .butler_utils import get_bias_files_butler


DEFAULT_BIAS_TYPE = 'spline'
SBIAS_TEMPLATE = 'analysis/superbias/templates/sbias_template.fits'
ALL_SLOTS = 'S00 S01 S02 S10 S11 S12 S20 S21 S22'.split()

mpl_utils.set_plt_ioff()

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
    def __init__(self, analysis_func, argnames=None):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        super(BiasAnalysisBySlot, self).__init__(analysis_func, get_bias_data, argnames)


class BiasAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over all the raft and then all the slots in a raft"""
    def __init__(self, analysis_func, argnames=None):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        super(BiasAnalysisByRaft, self).__init__(analysis_func, get_bias_data, argnames)


class BiasAnalysisFunc:
    """Simple functor class to tie together standard bias data analysis
    """

    # These need to be overridden by the sub-class
    analysisClass = None
    argnames = []

    def __init__(self, datasuffix="", extract_func=None, plot_func=None, **kwargs):
        """ C'tor
        @param datasuffix (func)        Suffix for filenames
        @param extract_func (func)      Function to extract table data
        @param plot_func (func)         Function to make plots
        @param kwargs:
           tablename_func (func)     Function to get output path for tables
           plotname_func (func)      Function to get output path for plots
        """
        self.datasuffix = datasuffix
        self.extract_func = extract_func
        self.plot_func = plot_func
        self.tablename_func = kwargs.get('tablename_func', slot_bias_tablename)
        self.plotname_func = kwargs.get('plotname_func', slot_bias_plotname)


    def make_datatables(self, butler, slot_data, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (Butler)   The data butler
        @param slot_data (dict)  Dictionary pointing to the bias and mask files
        @param kwargs

        @return (TableDict)
        """
        tablebase = self.tablename_func(suffix=self.datasuffix, **kwargs)
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if kwargs.get('skip', False) or self.extract_func is None:
            dtables = TableDict(output_data)
        else:
            dtables = self.extract_func(butler, slot_data, **kwargs)
            dtables.save_datatables(output_data)
        return dtables

    def make_plots(self, dtables):
        """Tie together the functions to make the data tables
        @param dtables (TableDict)   The data tables

        @return (FigureDict)
        """
        figs = FigureDict()
        if self.plot_func is not None:
            self.plot_func(dtables, figs)
        return figs

    def __call__(self, butler, slot_data, **kwargs):
        """Tie together the functions
        @param butler (Butler)   The data butler
        @param slot_data (dict)  Dictionary pointing to the bias and mask files
        @param kwargs
        """
        dtables = self.make_datatables(butler, slot_data, **kwargs)
        if kwargs.get('plot', False):
            figs = self.make_plots(dtables)
            if kwargs.get('interactive', False):
                figs.save_all(None)
            else:
                plotbase = self.plotname_func(**kwargs)
                makedir_safe(plotbase)
                figs.save_all(plotbase)

    @classmethod
    def make(cls, butler, data, **kwargs):
        """Tie together the functions
        @param butler (Butler)   The data butler
        @param data (dict)  Dictionary pointing to the bias and mask files
        @param kwargs
        """
        obj = cls()
        obj(butler, data, **kwargs)

    @classmethod
    def run(cls):
        """Run the analysis"""
        functor = cls.analysisClass(cls.make, cls.argnames)
        functor.run()



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




def extract_superbias_stats_raft(butler, raft_data, **kwargs):
    """Extract the correlations between the serial overscan for each amp on a raft

    @param butler (Butler)   The data butler
    @param raft_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        outdir (str)         Output directory
    """
    slots = ALL_SLOTS

    kwcopy = kwargs.copy()
    if butler is not None:
        sys.stdout.write("Ignoring butler in extract_superbias_stats_raft")
    if raft_data is not None:
        sys.stdout.write("Ignoring raft_data in extract_superbias_stats_raft")

    stats_data = {}
    for islot, slot in enumerate(slots):
        kwcopy['slot'] = slot
        mask_files = get_mask_files(**kwcopy)
        superbias = get_superbias_frame(mask_files=mask_files, **kwcopy)
        get_superbias_stats(None, superbias, stats_data,
                            islot=islot, slot=slot)

    dtables = TableDict()
    dtables.make_datatable('files', make_file_dict(None, slots))
    dtables.make_datatable('slots', dict(slots=slots))
    dtables.make_datatable('stats', stats_data)
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
    stat_type = kwargs.get('stat', None)
    if stat_type is None:
        stat_type = DEFAULT_STAT_TYPE

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
                       subtract_mean=True,
                       **kwargs)
    else:
        plot_superbias(output_file, mask_files, **kwargs)





def make_bias_data_slot(butler, slot_data, **kwargs):
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
    ba = BiasAnalysisFunc("biasdata", extract_bias_data_slot, plot_bias_data_slot)
    ba(butler, slot_data, **kwargs)


def make_superbias_stats_raft(butler, raft_data, **kwargs):
    """Extract the correlations between the serial overscan for each amp on a raft

    @param butler (Butler)   The data butler
    @param raft_data (dict)  Dictionary pointing to the bias and mask files
    @param kwargs
        raft (str)           Raft in question, i.e., 'RTM-004-Dev'
        run_num (str)        Run number, i.e,. '6106D'
        outdir (str)         Output directory
    """
    ba = BiasAnalysisFunc('_stats', extract_superbias_stats_raft, plot_superbias_stats_raft,
                          tablename_func=raft_superbias_tablename,
                          plotname_func=raft_superbias_plotname)
    ba(butler, raft_data, **kwargs)
