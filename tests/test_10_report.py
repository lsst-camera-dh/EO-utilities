# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.base.link_utils module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.report_task import ReportRunTask,\
    ReportSummaryTask

from .utils import RUN_TASKS, RUN_OPTIONS, SUMMARY_OPTIONS


def test_report_run_task():
    """Test the MaskAddTask"""
    task = ReportRunTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_report_summary_task():
    """Test the EOResultsRaftTask"""
    task = ReportSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
