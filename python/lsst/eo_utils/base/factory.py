"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains a factory to build objects that run analyses
"""

from collections import OrderedDict

from .config_utils import setup_parser, parse_args_to_dict

class EOTaskFactory:
    """Small class to keep track of analysis tasks"""

    def __init__(self):
        """C'tor"""
        self._tasks = OrderedDict()

    def keys(self):
        """Returns the names of the tasks"""
        return self._tasks.keys()

    def values(self):
        """Returns the `BaseAnalysisTask` objects"""
        return self._tasks.values()

    def items(self):
        """Retruns the name : task pairs"""
        return self._tasks.items()

    def __getitem__(self, key):
        """Get a single `BaseAnalysisTask` object by namne"""
        return self._tasks[key]

    def add_task_class(self, key, task_class):
        """Add an item to the dictionary

        This uses the default construct of the task class to build
        an instance of the class.

        Parameters
        ----------
        key : `str`
            The task name
        task_class : `class`
            The class
        """
        task = task_class()
        if key not in self._tasks:
            self._tasks[key] = task

    def run_task(self, key, **kwargs):
        """Run the selected task

        Parameters
        ----------
        key : `str`
            The task name
        kwargs
            Passed to the task's handler to invoke the task
        """
        task = self._tasks[key]
        handler = task.iteratorClass(task)
        handler.run_with_args(**kwargs)

    def build_parser(self, task_names=None, **kwargs):
        """Build and argument parser for a set of defined tasks

        Parameters
        ----------
        task_names : `list`
            The tasks to include
        kwargs
            Used to add more parameters to the argument parser

        Returns
        -------
        parser : `ArgumentParser`
            The parser, filled with the options defined for the task in this dictionary

        subparser_dict : `dict`
            All the sub-parsers, keyed by name
        """
        if task_names is None:
            task_names = self._tasks.keys()

        parser = setup_parser(**kwargs)
        supparsers = parser.add_subparsers(dest='task', help='sub-command help')

        subparser_dict = {}
        for task_name in task_names:
            task = self._tasks[task_name]
            subparser = supparsers.add_parser(task_name, help=task.__doc__)
            task.add_parser_arguments(subparser)
            subparser_dict[task_name] = subparser

        return parser, subparser_dict

    def parse_and_run(self, **kwargs):
        """Run a task using the command line arguments

        Parameters
        ----------
        kwargs
            Used to override command line arguments
        """
        parser, subparser_dict = self.build_parser(usage="eo_task.py")
        args = parser.parse_args()
        arg_dict = parse_args_to_dict(args, parser, subparser_dict)
        arg_dict.update(**kwargs)

        self.run_task(args.task, **arg_dict)

    def sort_tasks(self):
        """Generate dictionary of tasks sorted by level and datatype"""
        level_dict = {}
        for task_name, task in self.items():
            level = task.iteratorClass.level
            if level not in level_dict:
                level_dict[level] = {}
            datatype_dict = level_dict[level]
            if task.datatype not in datatype_dict:
                datatype_dict[task.datatype] = {}
            task_dict = datatype_dict[task.datatype]
            task_dict[task_name] = task
        return level_dict

    def make_csv(self, stream):
        """Generate a markdown table describing all the tasks"""
        stream.write("Task, Level, Dataype, Description\n")
        level_dict = self.sort_tasks()

        for _, datatype_dict in level_dict.items():
            for _, task_dict in datatype_dict.items():
                for task_name, task in task_dict.items():
                    task.csv_line(task_name, stream)


    def make_markdown(self, stream):
        """Generate a markdown table describing all the tasks"""
        stream.write("|| Task || Level || Datatype || Description ||\n")
        level_dict = self.sort_tasks()
        for _, datatype_dict in level_dict.items():
            for _, task_dict in datatype_dict.items():
                for task_name, task in task_dict.items():
                    task.markdown_line(task_name, stream)


EO_TASK_FACTORY = EOTaskFactory()
