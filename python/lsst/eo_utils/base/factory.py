"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes for various types of analyses.
"""

from collections import OrderedDict

from .config_utils import setup_parser

class EOTaskFactory:
    """Small class to keep track of analysis tasks"""

    def __init__(self):
        """C'tor"""
        self._tasks = OrderedDict()

    def keys(self):
        """@returns (list) the types of file names"""
        return self._tasks.keys()

    def values(self):
        """@returns (list) the `BaseAnalysisTask` objects """
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

        @param key (str)            The key
        @param task_class (class)   The class

        @returns (`FilenameFormat`) The newly create object
        """
        task = task_class()
        if key in self._tasks:
            raise KeyError("Key %s is already in EOTaskFactory" % key)
        self._tasks[key] = task


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
            task = self._tasks[task_name]
            subparser = supparsers.add_parser(task_name, help=task.__doc__)
            task.add_parser_arguments(subparser)

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
