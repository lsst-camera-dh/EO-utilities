# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.base.link_utils module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.link_utils import link_ts8_files

from lsst.eo_utils.base.mask_analysis import MaskAddTask

from lsst.eo_utils.base.eo_results import EOResultsRaftTask, EOResultsSummaryTask

from .utils import RUN_TASKS, RUN_OPTIONS, SUMMARY_OPTIONS

LINK_OPTIONS = dict(run='6106D', raft='RTM-004',
                    outdir='test_out', teststand='ts8', 
                    mapping='tests/test_ts8_mapping.yaml')

def test_link_ts8():
    """Test linking input ts8 files"""
    link_ts8_files(LINK_OPTIONS)

def test_link_bot():
    """Test linking input BOT files"""
    #FIXME
    #link_bot_files(**LINK_OPTIONS)
    return

def test_mask_add_task():
    """Test the MaskAddTask"""
    task = MaskAddTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_eo_results_raft_task():
    """Test the EOResultsRaftTask"""
    task = EOResultsRaftTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_eo_results_summary_task():
    """Test the EOResultsSummaryTask"""
    task = EOResultsSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
