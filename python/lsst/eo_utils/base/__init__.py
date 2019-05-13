"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes and other general utilities.
"""

# from .defaults import *
# from .config_utils import EOUtilOptions, Configurable

# from . import mpl_utils

# from .batch_utils import dispatch_job
# from . import butler_utils

from . import image_utils

from . import file_utils

from .data_utils import TableDict, vstack_tables

from .plot_utils import FigureDict

from .analysis import BaseAnalysisConfig, BaseAnalysisTask,\
    AnalysisConfig, AnalysisTask

from .iter_utils import AnalysisHandlerConfig, AnalysisHandler,\
    SimpleAnalysisHandler, AnalysisIterator,\
    AnalysisBySlotConfig, AnalysisBySlot,\
    AnalysisByRaftConfig, AnalysisByRaft, TableAnalysisByRaft,\
    SummaryAnalysisIterator

from .factory import EO_TASK_FACTORY

from .mask_analysis import MaskAddConfig, MaskAddTask

from .eo_results import EOResultsRaftConfig, EOResultsRaftTask,\
    EOResultsSummaryConfig, EOResultsSummaryTask
