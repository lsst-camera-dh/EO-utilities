"""Functions to analyse bias and superbias frames"""

import sys

from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.file_utils import makedir_safe

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot, AnalysisByRaft

from .file_utils import get_bias_files_run,\
    slot_bias_tablename, slot_bias_plotname

from .butler_utils import get_bias_files_butler


DEFAULT_BIAS_TYPE = 'spline'
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
    """Small class to iterate an analysis function over all the slots in a raft"""

    data_func = get_bias_data

    def __init__(self, analysis_func):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        """
        AnalysisBySlot.__init__(self, analysis_func)


class BiasAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis task over all the raft and then all the slots in a raft"""

    data_func = get_bias_data

    def __init__(self, analysis_func):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        """
        AnalysisByRaft.__init__(self, analysis_func)


class BiasAnalysisFunc:
    """Simple functor class to tie together standard bias data analysis
    """

    # These can overridden by the sub-class
    iteratorClass = BiasAnalysisBySlot
    argnames = []
    tablename_func = slot_bias_tablename
    plotname_func = slot_bias_plotname

    def __init__(self, datasuffix=""):
        """ C'tor
        @param datasuffix (str)        Suffix for filenames
        @param kwargs:
        """
        self.datasuffix = datasuffix

    def make_datatables(self, butler, data, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (`Butler`)   The data butler
        @param data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs

        @return (TableDict)
        """
        tablebase = self.tablename_func(suffix=self.datasuffix, **kwargs)
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if kwargs.get('skip', False):
            dtables = TableDict(output_data)
        else:
            dtables = self.extract(butler, data, **kwargs)
            dtables.save_datatables(output_data)
        return dtables

    def make_plots(self, dtables):
        """Tie together the functions to make the data tables
        @param dtables (`TableDict`)   The data tables

        @return (`FigureDict`) the figues we produced
        """
        figs = FigureDict()
        self.plot(dtables, figs)
        return figs

    def __call__(self, butler, data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        dtables = self.make_datatables(butler, data, **kwargs)
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
        functor = cls.iteratorClass(cls.make)
        functor.run()

    @staticmethod
    def extract(butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("BiasAnalysisFunc.extract")

    @staticmethod
    def plot(dtables, figs):
        """This needs to be implemented by the sub-class"""
        if dtables is not None and figs is not None:
            sys.stdout.write("Warning, plotting function not implemented\n")
