"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains tasks to analyze sflat exposures
"""

from . import file_utils as sflat_file_utils

from .analysis import SflatAnalysisConfig, SflatAnalysisTask

from .meta_analysis import SflatSlotTableAnalysisConfig,\
    SflatSlotTableAnalysisTask,\
    SflatRaftTableAnalysisConfig, SflatRaftTableAnalysisTask,\
    SflatSummaryAnalysisConfig, SflatSummaryAnalysisTask

from .superflat import SuperflatConfig, SuperflatTask,\
    SuperflatRaftConfig, SuperflatRaftTask

from .stability import StabilityConfig, StabilityTask

from .sflat_ratio import SflatRatioConfig, SflatRatioTask

from .sflat_cte import CTEConfig, CTETask
