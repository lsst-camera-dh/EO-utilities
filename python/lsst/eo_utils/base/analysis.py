"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes for analysis tasks.
"""

import lsst.pex.config as pexConfig

from .defaults import DEFAULT_STAT_TYPE

from .file_utils import makedir_safe, SLOT_BASE_FORMATTER,\
    MASK_FORMATTER, SUPERBIAS_FORMATTER, SUPERBIAS_STAT_FORMATTER

from .config_utils import EOUtilOptions, Configurable

from .data_utils import TableDict

from .plot_utils import FigureDict

from .iter_utils import SimpleAnalysisHandler

from .image_utils import get_ccd_from_id

class BaseAnalysisConfig(pexConfig.Config):
    """Configuration for EO analysis tasks"""


class BaseAnalysisTask(Configurable):
    """Base class for EO testing analysis tasks

    At minimum, sub-classes will need to implement the
    __call__ function to perform the data analysis.

    This class define the interaction between the sub-class
    and an iterator that can invoke the sub-class repeatedly
    with different input data.

    Sub-classes should also override these static members:

    ConfigClass : this should be set to a `BaseAnalysisConfig` sub-class
                  that defines the configuration parameters needed by the sub-class
    _DefaultName : typically this is set to the name of the sub-class,
                   this is used as a key by the factory class to find objects of the sub-class
    iteratorClass : this should be set to a `AnalysisHandler` sub-class that
                    can provide data for the sub-class
    """
    # These can overridden by the sub-class
    ConfigClass = BaseAnalysisConfig
    _DefaultName = "BaseAnalysisTask"
    iteratorClass = SimpleAnalysisHandler

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        Configurable.__init__(self, **kwargs)

    def __call__(self, butler, data, **kwargs):
        """Perform the data analysis

        It is up to the iteratorClass to construct the data object that is
        passed to this function.

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration
        """
        raise NotImplementedError('BaseAnalysisTask.__call__')

    def make_iterator(self):
        """Construct an object to iterate this task.

        Returns
        -------
        ret_val : `iteratorClass`
            An analysis iterator that can construct
            the input data structure and invoke this for a particular run, raft, ccd...
        """
        return self.iteratorClass(self)

    def get_config_param(self, key, default):
        """Gets the value of a parameter for the configuration
        and returns a default if the configuration does
        not contain that key.

        This useful when task with different parameters call the same function.

        Parameters
        ----------
        key : `str`
            The configuration parameter name
        default
            The value to use if the parameter is not in the configuration

        Returns
        -------
        The parameter value
        """
        if key in self.config.keys():
            return getattr(self.config, key)
        return default

    def get_filename_from_format(self, formatter, suffix, **kwargs):
        """Use a `FilenameFormat` object to construct a filename for a
        specific set of input parameters.

        Parameters
        ----------
        formater : `FilenameFormat`
            Defines how to construct the filename
        suffix : `str`
            Appended to the filename
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The resulting filename
        """
        format_key_dict = formatter.key_dict()
        format_vals = self.extract_config_vals(format_key_dict)
        format_vals.update(**kwargs)
        if suffix is not None:
            format_vals['suffix'] = suffix
        if self.get_config_param('stat', None) in [DEFAULT_STAT_TYPE, None]:
            format_vals['stat'] = 'superbias'
        return formatter(**format_vals)


    def get_superbias_file(self, suffix, **kwargs):
        """Get the name of the superbias file for a particular run, raft, ccd...

        Parameters
        ----------
        suffix : `str`
            Appended to the filename
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The filename
        """
        if self.get_config_param('stat', None) in [DEFAULT_STAT_TYPE, None]:
            formatter = SUPERBIAS_FORMATTER
        else:
            formatter = SUPERBIAS_STAT_FORMATTER

        return self.get_filename_from_format(formatter, suffix, **kwargs)


    def get_mask_files(self, **kwargs):
        """Get the list of mask files for a specific set of input parameters.

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `list`
            The resulting list of mask files
        """
        self.safe_update(**kwargs)
        if self.config.mask:
            return [self.get_filename_from_format(MASK_FORMATTER, "_mask.fits")]
        return []

    @classmethod
    def add_parser_arguments(cls, parser):
        """Add parser arguments for this class

        Parameters
        ----------
        parser : `ArgumentParser`
            The parser to add arguments to
        """
        functor = cls()
        handler = cls.iteratorClass(functor)
        handler.add_parser_arguemnts(parser)

    @classmethod
    def parse_and_run(cls):
        """Run the task using the command line arguments"""
        functor = cls()
        handler = cls.iteratorClass(functor)
        handler.run_analysis()

    @classmethod
    def run(cls, **kwargs):
        """Run the analysis using the keyword arguments

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        functor = cls()
        handler = cls.iteratorClass(functor)
        handler.run_with_args(**kwargs)



class AnalysisConfig(BaseAnalysisConfig):
    """Configuration for EO analysis tasks"""
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')


class AnalysisTask(BaseAnalysisTask):
    """Simple class to tie together standard data analysis elements

    This splits the __call__ function into two functions that
    will need to be implemented by sub-classes:

    1) extract() function that analyzes the input data and creates a set of tables
    in a `TableDict` object
    2) plot() function that uses a `TableDict` object create a set of
    plots and fill a `FigureDict` object

    This class also provides static members that construct the name of the files
    the `TableDict` and plotted figures are written to:

    tablename_format : a `FilenameFormat` object that builds the name of the file
                       the `TableDict` object produced by extract() is written to
    plotname_format : a `FilenameFormat` object that builds the base of the filenames
                      for the figures made by plot()

    Note that the ConfigClass.outsuffix parameter will be used in the construction
    of both types of filenames.

    """
    # These can overridden by the sub-class
    ConfigClass = AnalysisConfig
    _DefaultName = "AnalysisTask"
    iteratorClass = SimpleAnalysisHandler

    tablename_format = SLOT_BASE_FORMATTER
    plotname_format = SLOT_BASE_FORMATTER

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        BaseAnalysisTask.__init__(self, **kwargs)

    def get_suffix(self, **kwargs):
        """Get the suffix to add to table and plot filenames

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The suffix
        """
        self.safe_update(**kwargs)
        return self.config.outsuffix

    def tablefile_name(self, **kwargs):
        """Get the name of the file for the output tables for a particular
        run, raft, ccd..

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The name of the file
        """
        return self.get_filename_from_format(self.tablename_format,
                                             self.get_suffix(),
                                             **kwargs)

    def plotfile_name(self, **kwargs):
        """Get the basename for the plot files for a particular run, raft, ccd...

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The name of the file
        """
        return self.get_filename_from_format(self.plotname_format,
                                             self.get_suffix(),
                                             **kwargs)

    def get_superbias_frame(self, mask_files, **kwargs):
        """Get the superbias frame for a particular run, raft, ccd...

        Parameters
        ----------
        mask_files : `list`
            Files used to construct the pixel mask
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `MaskedCCD`
            The superbias frame
        """
        self.safe_update(**kwargs)
        if self.config.superbias is None:
            return None
        superbias_file = self.get_superbias_file('.fits')
        return get_ccd_from_id(None, superbias_file, mask_files)

    def make_datatables(self, butler, data, **kwargs):
        """Construct or read back the `TableDict` object with the analysis results

        It is up to the iteratorClass to construct the data object that is
        passed to this function.

        If the config.skip parameter is set, the `TableDict` object will be
        read back instead of generated

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The object that stores the output data
        """
        self.safe_update(**kwargs)

        tablebase = self.tablefile_name()
        makedir_safe(tablebase)
        output_data = tablebase + ".fits"

        if self.config.skip:
            dtables = TableDict(output_data)
        else:
            dtables = self.extract(butler, data)
            if dtables is not None:
                dtables.save_datatables(output_data)
                print("Writing %s" % output_data)
        return dtables

    def make_plots(self, dtables, **kwargs):
        """Make and save the files with the analysis plots

        If the config.plot parameter is not set this function will
        not be called
        If it is set to 'display' the figures will be show on the display
        If it is set to anything else (such as png, pdf...), that will be
        treated as the file type to write the figures as

        Parameters
        ----------
        dtables : `TableDict`
            The object that stores the output data

        Returns
        -------
        figs : `FigureDict`
            The resulting figures
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
        """Perform the data analysis

        It is up to the iteratorClass to construct the data object that is
        passed to this function.

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration
         """
        self.safe_update(**kwargs)
        dtables = self.make_datatables(butler, data)
        if self.config.plot is not None:
            self.make_plots(dtables)

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class

        It should analyze the input data and create a set of tables
        in a `TableDict` object

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class

        It should use a `TableDict` object to create a set of
        plots and fill a `FigureDict` object

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
