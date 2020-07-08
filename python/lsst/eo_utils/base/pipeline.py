"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes for analysis tasks.
"""

import lsst.pex.config as pexConfig

from .config_utils import EOUtilOptions

from .analysis import BaseTask, BaseConfig

from .iter_utils import SimpleAnalysisHandler


class MetaConfig(BaseConfig):
    """Configuration for EO analysis tasks"""

    @classmethod
    def add_task(cls, key, task_class):
        """Build parameter from for a particular Task

        Parameters
        ----------
        key : `str`
            The name to name the new attribute

        task_class : `class`
            Class of task of build parameter for

        Returns
        -------
        ret_val : `pexConfig.ConfigurableField`
            Parameter connect to the task class
        """
        param = EOUtilOptions.task_param(task_class)
        setattr(cls, key, param)
        return param


class MetaTask(BaseTask):
    """Base class for tasks that run other tasks

    """

    # These can overridden by the sub-class
    ConfigClass = MetaConfig
    _DefaultName = "MetaTask"
    iteratorClass = SimpleAnalysisHandler

    datatype = 'meta'

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        super().__init__(**kwargs)
        for key, val in self.ConfigClass._fields.items():
            if isinstance(val, pexConfig.configurableField.ConfigurableField):
                self.makeSubtask(key)

    def __call__(self, **kwargs):
        """Perform the data analysis

        It is up to the iteratorClass to construct the data object that is
        passed to this function.

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)
        top_dict = self.config.toDict()
        for key, val in self.ConfigClass._fields.items():
            if isinstance(val, pexConfig.configurableField.ConfigurableField):
                subtask = getattr(self, key)
                subtask.run_self(**top_dict)
