"""Utilities for offline data analysis of LSST Electrical-Optical testing"""

import sys

from .file_utils import makedir_safe

from .data_utils import TableDict

from .plot_utils import FigureDict

from .iter_utils import SimpleAnalysisHandler

def dummy_namefunc(**kwargs):
    """Dummy function to return a filename """
    raise NotImplementedError("dummy_namefunc called with %s" %kwargs)


class AnalysisFunc:
    """Simple functor class to tie together standard data analysis
    """

    # These can overridden by the sub-class
    iteratorClass = SimpleAnalysisHandler
    argnames = []
    tablename_func = dummy_namefunc
    plotname_func = dummy_namefunc

    def __init__(self, datasuffix=""):
        """ C'tor
        @param datasuffix (str)        Suffix for filenames
        @param kwargs:
        """
        self.datasuffix = datasuffix

    @classmethod
    def make_datatables(cls, butler, data, datasuffix, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (`Butler`)    The data butler
        @param data (dict)          Dictionary pointing to the bias and mask files
        @param datasuffix (str)     Suffix for filenames
        @param kwargs

        @return (TableDict)
        """
        kwargs['suffix'] = datasuffix
        tablebase = cls.tablename_func(**kwargs)
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if kwargs.get('skip', False):
            dtables = TableDict(output_data)
        else:
            dtables = cls.extract(butler, data, **kwargs)
            dtables.save_datatables(output_data)
        return dtables

    @classmethod
    def make_plots(cls, dtables, **kwargs):
        """Tie together the functions to make the data tables
        @param dtables (`TableDict`)   The data tables

        @return (`FigureDict`) the figues we produced
        """
        figs = FigureDict()
        cls.plot(dtables, figs)
        if kwargs.get('interactive', False):
            figs.save_all(None)
            return figs

        plotbase = cls.plotname_func(**kwargs)
        makedir_safe(plotbase)
        figs.save_all(plotbase)
        return None

    def __call__(self, butler, data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        dtables = self.make_datatables(butler, data, self.datasuffix, **kwargs)
        if kwargs.get('plot', False):
            self.make_plots(dtables, **kwargs)

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
        functor = cls.iteratorClass(cls.make, cls.argnames)
        functor.run_analysis()

    @staticmethod
    def extract(butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise RuntimeError("AnalysisFunc.extract is not overridden")

    @staticmethod
    def plot(dtables, figs):
        """This needs to be implemented by the sub-class"""
        if dtables is not None and figs is not None:
            sys.stdout.write("Warning, plotting function not implemented\n")
