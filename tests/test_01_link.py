# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.base.link_utils module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.link_utils import link_ts8_files, link_bot_files

from lsst.eo_utils.base.mask_analysis import MaskAddTask

from lsst.eo_utils.base.eo_results import EOResultsRaftTask, EOResultsSummaryTask

from .utils import requires_site, RUN_TASKS, RUN_OPTIONS, SUMMARY_OPTIONS

LINK_OPTIONS_TS8 = dict(run='6106D', raft='RTM-004',
                        outdir='test_out', teststand='ts8',
                        mapping='tests/test_ts8_mapping.yaml')

LINK_OPTIONS_BOT = dict(run='6545D', outdir='test_out', teststand='bot_etu',
                        mapping='tests/test_ts8_mapping.yaml')

@requires_site('slac')
def test_link_ts8():
    """Test linking input ts8 files"""
    link_ts8_files(LINK_OPTIONS_TS8)

@requires_site('slac')
def test_link_bot():
    """Test linking input BOT files"""
    link_bot_files(LINK_OPTIONS_BOT)

@requires_site('slac')
def test_mask_add_task():
    """Test the MaskAddTask"""
    task = MaskAddTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

@requires_site('slac')
def test_eo_results_raft_task():
    """Test the EOResultsRaftTask"""
    task = EOResultsRaftTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

@requires_site('slac')
def test_eo_results_summary_task():
    """Test the EOResultsSummaryTask"""
    task = EOResultsSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
