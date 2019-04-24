"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes for various types of analyses.
"""

import lsst.pex.config as pexConfig

from .file_utils import makedir_safe

from .config_utils import EOUtilConfig, Configurable

from .data_utils import TableDict

from .plot_utils import FigureDict

from .iter_utils import SimpleAnalysisHandler



class BaseAnalysisConfig(pexConfig.Config):
    """Configuration for EO analysis tasks"""
    butler_repo = EOUtilConfig.clone_param('butler_repo')


class BaseAnalysisTask(Configurable):
    """Simple functor class to tie together standard data analysis
    """
    ConfigClass = BaseAnalysisConfig
    _DefaultName = "BaseAnalysisTask"

    # These can overridden by the sub-class
    iteratorClass = SimpleAnalysisHandler

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        Configurable.__init__(**kwargs)

    def __call__(self, butler, data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        raise NotImplementedError('BaseAnalysisTask.__call__')

    @classmethod
    def parse_and_run(cls):
        """Run the analysis"""
        functor = cls()
        handler = cls.iteratorClass(functor)
        handler.run_analysis()


class AnalysisConfig(BaseAnalysisConfig):
    """Configuration for EO analysis tasks"""
    skip = EOUtilConfig.clone_param('skip')
    plot = EOUtilConfig.clone_param('plot')
    suffix = EOUtilConfig.clone_param('suffix')
    interactive = EOUtilConfig.clone_param('interactive')


class AnalysisTask(BaseAnalysisTask):
    """Simple functor class to tie together standard data analysis
    """
    ConfigClass = AnalysisConfig
    _DefaultName = "AnalysisTask"

    # These can overridden by the sub-class
    iteratorClass = SimpleAnalysisHandler

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        BaseAnalysisTask.__init__(self, **kwargs)

    def tablefile_name(self, **kwargs):
        """ Name of the file with the output tables

        @param kwargs:    Used to override configruation
        """
        raise NotImplementedError("AnalysisTask.tablefile_name")

    def plotfile_name(self, **kwargs):
        """ Name of the file for plots

        @param kwargs:    Used to override configruation
        """
        raise NotImplementedError("AnalysisTask.plotfile_name")

    def make_datatables(self, butler, data, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (`Butler`)    The data butler
        @param data (dict)          Dictionary pointing to the bias and mask files
        @param datasuffix (str)     Suffix for filenames
        @param kwargs

        @return (TableDict)
        """
        tablebase = self.tablefile_name(**kwargs)
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if self.config.skip:
            dtables = TableDict(output_data)
        else:
            dtables = self.extract(butler, data, **kwargs)
            dtables.save_datatables(output_data)
        return dtables

    def make_plots(self, dtables, **kwargs):
        """Tie together the functions to make the data tables
        @param dtables (`TableDict`)   The data tables

        @return (`FigureDict`) the figues we produced
        """
        figs = FigureDict()
        self.plot(dtables, figs, **kwargs)
        if self.config.interactive:
            figs.save_all(None)
            return figs

        plotbase = self.plotfile_name(**kwargs)
        makedir_safe(plotbase)
        figs.save_all(plotbase)
        return None

    def __call__(self, butler, data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        self.safe_update(**kwargs)
        dtables = self.make_datatables(butler, data, **kwargs)
        if self.config.plot:
            self.make_plots(dtables, **kwargs)

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
