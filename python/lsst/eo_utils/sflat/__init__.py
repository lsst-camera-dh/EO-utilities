"""Utilities for offline data analysis of LSST Electrical-Optical testing

This module contains tasks to analyze sflat exposures
"""

from .butler_utils import get_sflat_files_butler

from . import file_utils as sflat_file_utils

from .analysis import SflatAnalysisConfig, SflatAnalysisTask

from .meta_analysis import SflatSummaryAnalysisConfig, SflatSummaryAnalysisTask

from .superflat import SuperflatConfig, SuperflatTask

from .sflat_ratio import SflatRatioConfig, SflatRatioTask,\
    SflatRatioStatsConfig, SflatRatioStatsTask

