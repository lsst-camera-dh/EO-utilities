"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains base classes and other general utilities.
"""

#from .defaults import *
# from .config_utils import EOUtilOptions, Configurable

# from . import mpl_utils

# from .batch_utils import dispatch_job
# from . import butler_utils

# from . import defautls

from . import image_utils

from . import file_utils

from . import data_access

from .data_utils import TableDict, vstack_tables

from .plot_utils import FigureDict

from .calib_utils import CalibDict, DEFAULT_CALIB_DICT

from .analysis import BaseConfig, BaseTask,\
    BaseAnalysisConfig, BaseAnalysisTask,\
    AnalysisConfig, AnalysisTask

from .merge_utils import CameraMosaicConfig, CameraMosaicTask

from .iter_utils import AnalysisHandlerConfig, AnalysisHandler,\
    SimpleAnalysisHandler, AnalysisIterator,\
    AnalysisBySlotConfig, AnalysisBySlot,\
    AnalysisByRaftConfig, AnalysisByRaft,\
    TableAnalysisBySlot, TableAnalysisByRaft,\
    AnalysisByRunConfig, AnalysisByRun,\
    SummaryAnalysisIterator, SummaryAnalysisBySlotIterator

from .pipeline import MetaConfig, MetaTask

from .factory import EO_TASK_FACTORY

from .mask_analysis import MaskAddConfig, MaskAddTask

from .eo_results import EOResultsRaftConfig, EOResultsRaftTask,\
    EOResultsSummaryConfig, EOResultsSummaryTask

from .report_task import ReportConfig, ReportTask,\
    ReportSlotConfig, ReportSlotTask,\
    ReportRaftConfig, ReportRaftTask,\
    ReportRunConfig, ReportRunTask,\
    ReportSummaryConfig, ReportSummaryTask
