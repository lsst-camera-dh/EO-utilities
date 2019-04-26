"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes for various types of analyses.
"""

import lsst.pex.config as pexConfig

from .file_utils import makedir_safe, SLOT_BASE_FORMATTER,\
    MASK_FORMATTER, SUPERBIAS_FORMATTER

from .config_utils import EOUtilOptions, Configurable

from .data_utils import TableDict

from .plot_utils import FigureDict

from .iter_utils import SimpleAnalysisHandler

from .image_utils import get_ccd_from_id

class BaseAnalysisConfig(pexConfig.Config):
    """Configuration for EO analysis tasks"""


class BaseAnalysisTask(Configurable):
    """Simple functor class to tie together standard data analysis
    """
    # These can overridden by the sub-class
    ConfigClass = BaseAnalysisConfig
    _DefaultName = "BaseAnalysisTask"
    iteratorClass = SimpleAnalysisHandler


    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        Configurable.__init__(self, **kwargs)

    def __call__(self, butler, data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        raise NotImplementedError('BaseAnalysisTask.__call__')

    def make_iterator(self):
        """@returns (`AnalysisHandler`) an analysis iterator that using this task"""
        return self.iteratorClass(self)

    def get_filename_from_format(self, formatter, suffix, **kwargs):
        """Use a formatter to get a filename

        @param kwargs:    Used to override configruation
        """
        self.safe_update(**kwargs)
        format_key_dict = formatter.key_dict()
        format_vals = self.config.extract_config_vals(format_key_dict)
        format_vals['suffix'] = suffix
        return formatter(**format_vals)

    def get_mask_files(self, **kwargs):
        """Get the list of mask files

        @param kwargs:    Used to override configruation
        @returns (list)
        """
        self.safe_update(**kwargs)
        if self.config.mask:
            return [self.get_filename_from_format(MASK_FORMATTER, "")]
        return []

    @classmethod
    def add_parser_arguments(cls, parser):
        """Add parser arguments for this class

        @param parser (`ArgumentParser`)   The parser
        """
        functor = cls()
        handler = cls.iteratorClass(functor)
        handler.add_parser_arguemnts(parser)

    @classmethod
    def parse_and_run(cls):
        """Run the analysis using the command line arguments"""
        functor = cls()
        handler = cls.iteratorClass(functor)
        handler.run_analysis()

    @classmethod
    def run(cls, **kwargs):
        """Run the analysis using the keyword arguments"""
        functor = cls()
        handler = cls.iteratorClass(functor)
        handler.run_with_args(**kwargs)


class AnalysisConfig(BaseAnalysisConfig):
    """Configuration for EO analysis tasks"""
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class AnalysisTask(BaseAnalysisTask):
    """Simple functor class to tie together standard data analysis
    """
    # These can overridden by the sub-class
    ConfigClass = AnalysisConfig
    _DefaultName = "AnalysisTask"
    iteratorClass = SimpleAnalysisHandler

    tablename_format = SLOT_BASE_FORMATTER
    plotname_format = SLOT_BASE_FORMATTER

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        BaseAnalysisTask.__init__(self, **kwargs)

    def get_suffix(self, **kwargs):
        """Get the suffix to add to table and plotfiles

        @param kwargs:    Used to override configruation
        @returns (str)
        """
        self.safe_update(**kwargs)
        return self.config.outsuffix

    def tablefile_name(self, **kwargs):
        """Get the name of the file with the output tables

        @param kwargs:    Used to override configruation
        @returns (str)
        """
        self.safe_update(**kwargs)
        return self.get_filename_from_format(self.tablename_format,
                                             self.get_suffix())

    def plotfile_name(self, **kwargs):
        """Get the basename of the plot files

        @param kwargs:    Used to override configruation
        @returns (str)
        """
        self.safe_update(**kwargs)
        return self.get_filename_from_format(self.plotname_format,
                                             self.get_suffix())

    def get_superbias_file(self, **kwargs):
        """Get the superbias file

        @param kwargs:    Used to override configruation
        @returns (list)
        """
        self.safe_update(**kwargs)
        if self.config.superbias is None:
            return None
        return self.get_filename_from_format(SUPERBIAS_FORMATTER, "")

    def get_superbias_frame(self, mask_files, **kwargs):
        """Get the superbias frame

        @returns (`MaskedCCD`)      The frame
        """
        self.safe_update(**kwargs)
        superbias_file = self.get_superbias_file()
        if superbias_file is None:
            return None
        return get_ccd_from_id(None, superbias_file, mask_files)

    def make_datatables(self, butler, data, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (`Butler`)    The data butler
        @param data (dict)          Dictionary pointing to the bias and mask files
        @param datasuffix (str)     Suffix for filenames
        @param kwargs

        @return (TableDict)
        """
        self.safe_update(**kwargs)

        tablebase = self.tablefile_name()
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if self.config.skip:
            dtables = TableDict(output_data)
        else:
            dtables = self.extract(butler, data)
            dtables.save_datatables(output_data)
            print("Writing %s" % output_data)
        return dtables

    def make_plots(self, dtables, **kwargs):
        """Tie together the functions to make the data tables
        @param dtables (`TableDict`)   The data tables

        @return (`FigureDict`) the figues we produced
        """
        self.safe_update(**kwargs)

        figs = FigureDict()
        self.plot(dtables, figs)
        if self.config.plot == 'display':
            figs.save_all(None)
            return figs

        plotbase = self.plotfile_name()
        makedir_safe(plotbase)
        figs.save_all(plotbase, self.config.plot)
        return None

    def __call__(self, butler, data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        self.safe_update(**kwargs)
        dtables = self.make_datatables(butler, data)
        if self.config.plot is not None:
            self.make_plots(dtables)



    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
