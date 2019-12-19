"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes for analysis tasks.
"""

import abc

import os

import glob

import lsst.pex.config as pexConfig

from lsst.eotest.sensor import NonlinearityCorrection

from .defaults import DEFAULT_STAT_TYPE

from .file_utils import makedir_safe,\
    SLOT_BASE_FORMATTER, MASK_FORMATTER,\
    SUPERBIAS_FORMATTER, SUPERBIAS_STAT_FORMATTER,\
    NONLIN_FORMATTER, EORESULTSIN_FORMATTER

from .config_utils import EOUtilOptions, Configurable

from .calib_utils import CalibDict

from .data_utils import TableDict

from .plot_utils import FigureDict

from .iter_utils import SimpleAnalysisHandler

from .image_utils import get_ccd_from_id, get_raw_image

from .data_access import get_data_for_run, LOCATION_INFO_DICT


class BaseConfig(pexConfig.Config):
    """Configuration for EO analysis tasks"""
    calib_dict = EOUtilOptions.clone_param('calib_dict')
    calib = EOUtilOptions.clone_param('calib')

class BaseTask(Configurable):
    """Base class for EO testing tasks

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
    datatype : this is a string that defines what type of data a task runs over
               this is used to group the tasks and also to help find data
    """
    __metaclass__ = abc.ABCMeta

    # These can overridden by the sub-class
    ConfigClass = BaseConfig
    _DefaultName = "BaseTask"
    iteratorClass = SimpleAnalysisHandler
    datatype = 'None'


    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        Configurable.__init__(self, **kwargs)
        self._calib_file = None
        self._calib_dict = None
        self._load_calibration_dict()


    def _load_calibration_dict(self):
        """Load the calibration dictionary
        """
        if self._calib_file == self.config.calib_dict:
            return
        self._calib_file = self.config.calib_dict
        self._calib_dict = CalibDict(self._calib_file)

    @abc.abstractmethod
    def __call__(self, **kwargs):
        """Perform the data analysis

        It is up to the iteratorClass to construct the data object that is
        passed to this function.

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        raise NotImplementedError()

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

    def get_calib_param_from_flavor(self, key):
        """Gets the value of a calibration parameter for a particular flavor

        Parameters
        ----------
        key : `str`
            The calibration parameter name

        Returns
        -------
        The parameter value
        """
        self._load_calibration_dict()
        return self._calib_dict.get_calib_value_task(self.config.calib, self._name, key)


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

    def run_self(self, **kwargs):
        """Run the analysis using the keyword arguments

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        handler = self.iteratorClass(self)
        handler.run_with_args(**kwargs)

    def log_progress(self, msg):
        """Make an info message that we are running a particular slot

        Parameters
        ----------
        msg : `str`
            The message
        """
        self.log.info(msg)

    def csv_line(self, taskname, stream):
        """Write a line of comma-seperated values, used to build a table of task types"""
        stream.write("%s, %s, %s, %s\n" % (taskname,
                                           self.iteratorClass.level,
                                           self.datatype,
                                           self.__doc__.replace(',', '').replace('\n', '')))

    def markdown_line(self, taskname, stream):
        """Write a line of markdown, used to build a table of task types"""
        stream.write("| %s | %s | %s | %s |\n" % (taskname,
                                                  self.iteratorClass.level,
                                                  self.datatype,
                                                  self.__doc__.replace('\n', '')))


class BaseAnalysisConfig(BaseConfig):
    """Configuration for EO analysis tasks"""


class BaseAnalysisTask(BaseTask):
    """Sub-class for simple analyses

    """
    __metaclass__ = abc.ABCMeta

    # These can overridden by the sub-class
    ConfigClass = BaseAnalysisConfig
    _DefaultName = "BaseAnalysisTask"
    iteratorClass = SimpleAnalysisHandler

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
        raise NotImplementedError()

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
        if formatter is None:
            return None
        format_key_dict = formatter.key_dict()
        format_vals = self.extract_config_vals(format_key_dict)
        format_vals.update(**kwargs)
        ret_val = formatter(**format_vals)
        if suffix is not None:
            ret_val += suffix
        return ret_val

    def get_superbias_file(self, **kwargs):
        """Get the name of the superbias file for a particular run, raft, ccd...

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The filename
        """
        kwcopy = kwargs.copy()
        if self.get_config_param('stat', None) in [DEFAULT_STAT_TYPE, None]:
            formatter = SUPERBIAS_FORMATTER
        else:
            formatter = SUPERBIAS_STAT_FORMATTER

        sbias = self.get_calib_param_from_flavor('superbias')
        if sbias not in [None, 'none', 'None', False]:
            kwcopy['calib'] = sbias

        return self.get_filename_from_format(formatter, '.fits', **kwcopy)


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

        val = self.get_calib_param_from_flavor('mask')
        if val not in [None, 'none', 'None', False]:
            mask_files = glob.glob(self.get_filename_from_format(MASK_FORMATTER, ".fits",
                                                                 filekey='*-mask', calib=val))
            return mask_files
        return []


    def get_gains(self, **kwargs):
        """Get the gains for a specific set of input parameters.

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        gains : `array`
            The gains
        """
        self.safe_update(**kwargs)
        gain_type = self.get_calib_param_from_flavor('gain')
        if gain_type in [None, 'none', 'None', False]:
            return None
        gain_run = self.get_calib_param_from_flavor('gain_run')

        kwcopy = kwargs.copy()
        if gain_run not in [None, 'none', 'None']:
            kwcopy.setdefault('run', gain_run)

        gain_file = self.get_filename_from_format(EORESULTSIN_FORMATTER, '.fits',
                                                  calib=gain_type, filekey='results',
                                                  **kwcopy)
        try:
            tables = TableDict(gain_file)
        except FileNotFoundError:
            return None
        gain_table = tables['amplifier_results']
        return gain_table['GAIN']


    def get_nonlinearirty_correction(self, **kwargs):
        """Get the gains for a specific set of input parameters.

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ncl : `NonlinearityCorrection`
            The object that implements the correction
        """
        self.safe_update(**kwargs)
        nonlin = self.get_calib_param_from_flavor('nonlin')
        if nonlin in [False, None, 'none', 'None']:
            return None

        nonlin_file = self.get_filename_from_format(NONLIN_FORMATTER, '.fits',
                                                    calib=nonlin, filekey='flat-nonlin')

        nonlin_key_dict = dict(nonlin_spline_ext=None, nonlin_spline_smooth=None)
        nonlin_vals = self.extract_config_vals(nonlin_key_dict)
        kw_spline = {}
        if 'nonlin_spline_ext' in nonlin_vals:
            kw_spline['ext'] = nonlin_vals['nonlin_spline_ext']
        if 'nonlin_spline_smooth' in nonlin_vals:
            kw_spline['s'] = nonlin_vals['nonlin_spline_smooth']

        print(kw_spline)
        nlc = NonlinearityCorrection.create_from_fits_file(nonlin_file, **kw_spline)
        return nlc


    def log_info_slot_msg(self, config, msg):
        """Make an info message that we are running a particular slot

        Parameters
        ----------
        log : `lsst.log.log.log.Log`
            The log to write to

        config : `pexConfig`
            The object with the configuration to get the run, raft, slot

        msg : `str`
            The rest of the message
        """
        if hasattr(config, 'run'):
            run = config.run
        else:
            run = 'xx'
        if hasattr(config, 'raft'):
            raft = config.raft
        else:
            raft = 'xx'
        if hasattr(config, 'slot'):
            slot = config.slot
        else:
            slot = 'xx'
        self.log.info("Working on %s:%s:%s.  %s" % (run, raft, slot, msg))


    def log_info_raft_msg(self, config, msg):
        """Make an info message that we are running a particular raft

        Parameters
        ----------
        log : `lsst.log.log.log.Log`
            The log to write to

        config : `pexConfig`
            The object with the configuration to get the run, raft, slot

        msg : `str`
            The rest of the message
        """
        if hasattr(config, 'run'):
            run = config.run
        else:
            run = 'xx'
        if hasattr(config, 'raft'):
            raft = config.raft
        else:
            raft = 'xx'

        self.log.info("Working on %s:%s.  %s" % (run, raft, msg))


    def log_warn_slot_msg(self, config, msg):
        """Make an warning message

        Parameters
        ----------
        log : `lsst.log.log.log.Log`
            The log to write to

        config : `pexConfig`
            The object with the configuration to get the run, raft, slot

        msg : `str`
            The rest of the message
        """
        if hasattr(config, 'run'):
            run = config.run
        else:
            run = 'xx'
        if hasattr(config, 'raft'):
            raft = config.raft
        else:
            raft = 'xx'
        if hasattr(config, 'slot'):
            slot = config.slot
        else:
            slot = 'xx'
        self.log.warn("%s:%s:%s.  %s" % (run, raft, slot, msg))

    def log_progress(self, msg):
        """Make an info message that we are running a particular slot

        Parameters
        ----------
        msg : `str`
            The message
        """
        self.log.info(msg)


class AnalysisConfig(BaseAnalysisConfig):
    """Configuration for EO analysis tasks"""
    outdir = EOUtilOptions.clone_param('outdir')
    teststand = EOUtilOptions.clone_param('teststand')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    overwrite = EOUtilOptions.clone_param('overwrite')
    filekey = EOUtilOptions.clone_param('filekey')


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

    Note that the ConfigClass.filekey parameter will be used in the construction
    of both types of filenames.

    Finally, this class provides static data members should be overridden by sub-classes
    to define how they access data for a given run

    testtypes : `list` of `str` or `None`.
                A list of the types of test the sub-class used data from.
                `None` means to use the data from all the availble test types
                Legal values are defined in `data_access.TEST_TYPES`
    imagetype : `str` or `None`
                Used to define the type of image to get for a particular task
                `None` means to get the default image for a particular testtype

    """
    # These can overridden by the sub-class
    ConfigClass = AnalysisConfig
    _DefaultName = "AnalysisTask"
    iteratorClass = SimpleAnalysisHandler

    tablename_format = SLOT_BASE_FORMATTER
    plotname_format = SLOT_BASE_FORMATTER

    # This is use to define the types of tests to get data for
    testtypes = None
    # This is used to override the default image type
    imagetype = None
    # This is the list of plots, used to make sure that they exist
    plot_names = None

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        BaseAnalysisTask.__init__(self, **kwargs)
        self._handler_config = None

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
        return self.get_filename_from_format(self.tablename_format, '', **kwargs)

    def intablefile_name(self, **kwargs):
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
        kwcopy = kwargs.copy()

        try:
            kwcopy['filekey'] = self.config.infilekey
            has_infilekey = True
        except Exception:
            kwcopy['filekey'] = self.config.filekey
            has_infilekey = False

        if hasattr(self, 'intablename_format'):
            return self.get_filename_from_format(getattr(self, 'intablename_format'), '', **kwcopy)
        if not has_infilekey:
            return "None"
        try:
            return self.tablefile_name(**kwcopy)
        except Exception:
            pass
        return "None"

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
        return self.get_filename_from_format(self.plotname_format, '', **kwargs)


    def get_superbias_amp_image(self, butler, superbias_frame, amp):
        """Get the image for one amp for the superbias

        Parameters
        ----------
        butler : `Butler` or `None`
            Data Butler (or none)
        superbias_frame : `MaskedCCD` or `None`
            superbias image for the whole CCD
        amp : `int`
            Amplifier index

        Returns
        -------
        superbias_im : `ImageF`
            The image for the requested amplifier
        """
        offset = 0
        if self._handler_config is not None:
            if self._handler_config.data_source == 'butler':
                if butler is None:
                    raise ValueError("Data source == butler, but no butler present")
                offset = 1

        if superbias_frame is not None:
            superbias_im = get_raw_image(superbias_frame, amp+offset)
        else:
            superbias_im = None
        return superbias_im

    def get_bias_algo(self):
        """Get the name of the algorithm to remove bias with the overscan"""
        return self.get_calib_param_from_flavor('bias')


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


        if self.get_calib_param_from_flavor('superbias') in [False, None, 'none', 'None']:
            return None
        superbias_file = self.get_superbias_file()
        try:
            ccd = get_ccd_from_id(None, superbias_file, mask_files)
        except Exception:
            print("Failed to read", superbias_file)
            ccd = None
        return ccd

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
            try:
                dtables = TableDict(output_data)
            except IOError as msg:
                print(msg)
                dtables = None
            return dtables

        if not self.config.overwrite and os.path.exists(output_data):
            self.log.info("Ouput file %s exists, skipping extract()" % output_data)
            try:
                dtables = TableDict(output_data)
            except IOError as msg:
                print(msg)
                dtables = None
            self.set_local_data(butler, data, **kwargs)
            return dtables

        dtables = self.extract(butler, data)
        if dtables is not None:
            try:
                dtables.save_datatables(output_data)
                self.log.info("Writing %s" % output_data)
            except ValueError:
                self.log.warn("Failed to write table %s" % output_data)
        return dtables

    def set_local_data(self, butler, data, **kwargs):
        """Set local data members if extract fails

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration
        """
        _ = (butler, data, kwargs)
        self.log.info("  set_local_data()")


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
        self.log.info("Saving plots to %s" % plotbase)
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
        self._handler_config = kwargs.get('handler_config', None)
        dtables = self.make_datatables(butler, data)
        if dtables is None:
            self.log_warn_slot_msg(self.config, "extract() returned None")
            return
        if self.config.plot is not None:
            self.make_plots(dtables)


    def get_ccd(self, butler, data_id, mask_files, **kwargs):
        """CCD image from a data_id

        If we are using `Butler` then this will take a
        data_id `dict` ojbect and return an `ExposureF` object

        If we are not using `Butler` (i.e., if bulter is `None`)
        then this will take a filename and return a `MaskedCCD` object

        Parameters
        ----------
        butler : `Butler` or `None`
            Data Butler
        data_id : `dict` or `str`
            Data identier
        mask_files : `list`
            List of data_ids for the files to construct the pixel mask

        Keywords
        --------
        bias_frame : `ExposureF` or `MaskedCCD` or `None`
            Object with the bias data
        masked_ccd : `bool`
            Use bulter only to get filename, return as MaskedCCD object

        Returns
        -------
        ccd : `ExposureF` or `MaskedCCD`
            CCD data object
        """
        if self._handler_config is not None:
            use_masked_ccd = self._handler_config.data_source == 'butler_file'
            kwargs.setdefault('masked_ccd', use_masked_ccd)
        return get_ccd_from_id(butler, data_id, mask_files, **kwargs)

    @abc.abstractmethod
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
        raise NotImplementedError()

    @abc.abstractmethod
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
        raise NotImplementedError()


    @classmethod
    def get_data(cls, butler, run_num, **kwargs):
        """Get a set of bias and mask files out of a folder

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        kwargs.pop('run', None)

        imagetype = cls.imagetype

        if imagetype is None:
            imagetype = LOCATION_INFO_DICT[cls.testtypes[0]].get_imagetype(**kwargs)

        return get_data_for_run(butler, run_num,
                                testtypes=cls.testtypes,
                                imagetype=imagetype,
                                outkey=cls.datatype.upper(),
                                **kwargs)


    def io_csv_line(self, taskname, stream):
        """Write a line of comma-seperated values, used to build a table of task types"""

        md_dict = dict(raft="<RAFT>", run="<RUN>", slot="<SLOT>", dataset="<DATASET>")

        infilename = self.intablefile_name(**md_dict).replace('analysis/bot/', '')
        table_file = self.tablefile_name(**md_dict).replace('analysis/bot/', '')
        plot_file = self.plotfile_name(**md_dict).replace('analysis/bot/', '')

        stream.write("%-25s %-60s %-60s %-60s\n" % (taskname,
                                                    infilename,
                                                    table_file,
                                                    plot_file))


    def io_markdown_line(self, taskname, stream):
        """Write a line of markdown, used to build a table of task types"""
        md_dict = dict(raft="<RAFT>", run="<RUN>", slot="<SLOT>", dataset="<DATASET>")

        infilename = self.intablefile_name(**md_dict).replace('analysis/bot/', '')
        table_file = self.tablefile_name(**md_dict).replace('analysis/bot/', '')
        plot_file = self.plotfile_name(**md_dict).replace('analysis/bot/', '')

        stream.write("| %s | %s | %s | %s |\n" % (taskname,
                                                  infilename,
                                                  table_file,
                                                  plot_file))


    def print_plot_names(self, taskname, stream):
        """Write a few lines with the names of expected plots"""
        md_dict = dict(raft="{raft}", run="{run}", slot="{slot}", dataset="{dataset}")

        plotbase = self.plotfile_name(**md_dict)
        if self.plot_names is None:
            stream.write('%s: plots not defined.\n' % taskname)
            return

        stream.write('%s\n' % taskname)
        for plot_name in self.plot_names:
            stream.write('  %s_%s.png\n' % (plotbase, plot_name))
