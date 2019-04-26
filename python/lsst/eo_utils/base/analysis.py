"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes for various types of analyses.
"""

from collections import OrderedDict

import lsst.pex.config as pexConfig

from .file_utils import makedir_safe, SLOT_BASE_FORMATTER

from .config_utils import EOUtilOptions, Configurable, setup_parser

from .data_utils import TableDict

from .plot_utils import FigureDict

from .iter_utils import SimpleAnalysisHandler



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
    suffix = EOUtilOptions.clone_param('suffix')


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

    def tablefile_name(self, **kwargs):
        """ Name of the file with the output tables

        @param kwargs:    Used to override configruation
        """
        return self.tablename_format(**kwargs)


    def plotfile_name(self, **kwargs):
        """ Name of the file for plots

        @param kwargs:    Used to override configruation
        """
        return self.plotname_format(**kwargs)

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
            print("Writing %s" % output_data)
        return dtables

    def make_plots(self, dtables, **kwargs):
        """Tie together the functions to make the data tables
        @param dtables (`TableDict`)   The data tables

        @return (`FigureDict`) the figues we produced
        """
        figs = FigureDict()
        self.plot(dtables, figs, **kwargs)
        if self.config.plot == 'display':
            figs.save_all(None)
            return figs

        plotbase = self.plotfile_name(**kwargs)
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
        dtables = self.make_datatables(butler, data, **kwargs)
        if self.config.plot is not None:
            self.make_plots(dtables, **kwargs)

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")



class EOTaskFactory:
    """Small class to keep track of analysis tasks"""

    def __init__(self):
        """C'tor"""
        self._tasks = OrderedDict()

    def keys(self):
        """@returns (list) the types of file names"""
        return self._tasks.keys()

    def values(self):
        """@returns (list) the `FilenameFormat` objects """
        return self._tasks.values()

    def items(self):
        """@returns (list) the key-value pairs"""
        return self._tasks.items()

    def __getitem__(self, key):
        """Get a single item

        @param key (str)               The key
        @returns (`BaseAnalysisTask`)  The corresponding task
        """
        return self._tasks[key]

    def add_task_class(self, key, task_class):
        """Add an item to the dict

        @param task_class (class)   The class

        @returns (`FilenameFormat`) The newly create object
        """
        if key in self._tasks:
            raise KeyError("Key %s is already in EOTaskFactory" % key)
        self._tasks[key] = task_class


    def __call__(self, key, **kwargs):
        """Construnct an object of the selected class

        @param key (str)            The key
        @param kwargs               Passed to the object c'tor

        @returns (`BaseAnalysisTask`)
        """
        return self._tasks[key](**kwargs)

    def run_task(self, key, **kwargs):
        """Run the selected task

        @param key (str)            The key
        @param kwargs               Passed to the `FilenameFormat` object

        @returns (str) The corresponding filename
        """
        task_class = self._tasks[key]
        task_class.run(**kwargs)

        
    def build_parser(self, task_names=None, **kwargs):
        """Build and argument parser for a set of defined tasks

        @param task_names (list)    The tasks to include
        
        @returns (`ArgumentParser`) The parser
        """
        if task_names is None:
            task_names = self._tasks.keys()

        parser = setup_parser(**kwargs)
        supparsers = parser.add_subparsers(dest='task', help='sub-command help')

        for task_name in task_names:
            task_class = self._tasks[task_name]
            subparser = supparsers.add_parser(task_name, help=task_class.__doc__)
            task_class.add_parser_arguments(subparser)
        
        return parser

    def parse_and_run(self, **kwargs):
        """Run a task using the command line arguments"""
        parser = self.build_parser(usage="eo_task.py")
        args = parser.parse_args()

        arg_dict = args.__dict__.copy()
        arg_dict = args.__dict__.copy()
        arg_dict.update(**kwargs)

        self.run_task(args.task, **arg_dict)


EO_TASK_FACTORY = EOTaskFactory()
