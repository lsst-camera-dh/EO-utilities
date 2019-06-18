# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.dark module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import dark
from lsst.eo_utils.dark.file_utils import get_dark_files_run

from .utils import RUN_TASKS

RUN_OPTIONS = dict(runs=['6106D'], bias='spline',
                   superbias='spline', outdir='test_out', plot='png')
SUMMARY_OPTIONS = dict(dataset='test', bias='spline',
                       superbias='spline', outdir='test_out', plot='png')

def test_dark_file_utils():
    """Test the dark.file_utils module"""
    dark_files_6106 = get_dark_files_run('6106D')
    assert len(dark_files_6106) == 1
    assert 'RTM-004' in dark_files_6106
    assert len(dark_files_6106['RTM-004']) == 9
    assert len(dark_files_6106['RTM-004']['S00']) == 1
    assert 'DARK' in dark_files_6106['RTM-004']['S00']
    assert len(dark_files_6106['RTM-004']['S00']['DARK']) == 5

    dark_files_6545 = get_dark_files_run('6545D')
    assert len(dark_files_6545) == 2
    assert 'R10' in dark_files_6545
    assert len(dark_files_6545['R10']) == 9
    assert len(dark_files_6545['R10']['S00']) == 1
    assert 'DARK' in dark_files_6545['R10']['S00']
    assert len(dark_files_6545['R10']['S00']['DARK']) == 5


def test_dark_butler_utils():
    """Test the dark.butler_utils module"""
    return

def test_superdark():
    """Test the SuperdarkTask"""
    task = dark.SuperdarkTask()
    if RUN_TASKS:
        task.run(nfiles=2, **RUN_OPTIONS)

def test_superdark_raft():
    """Test the SuperdarkRaftTask"""
    task = dark.SuperdarkRaftTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_dark_current():
    """Test the DarkCurrentTask"""
    task = dark.DarkCurrentTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_dark_current_sum():
    """Test the DarkCurrentSummaryTask"""
    task = dark.DarkCurrentSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
