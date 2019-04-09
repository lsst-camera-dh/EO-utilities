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

    @param: butler (`Bulter`)  The data Butler
    @param run_num (str)        The number number we are reading
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
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
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
        @param dtables (`TableDict`)   The data tables

        @return (`FigureDict`) the figues we produced
        """
        figs = FigureDict()
        if self.plot_func is not None:
            self.plot_func(dtables, figs)
        return figs

    def __call__(self, butler, slot_data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
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
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        obj = cls()
        obj(butler, data, **kwargs)

    @classmethod
    def run(cls):
        """Run the analysis"""
        functor = cls.analysisClass(cls.make, cls.argnames)
        functor.run()

