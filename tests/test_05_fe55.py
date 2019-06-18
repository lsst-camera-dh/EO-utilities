# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.fe55 module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import fe55
from lsst.eo_utils.fe55.file_utils import get_fe55_files_run

from .utils import RUN_TASKS

RUN_OPTIONS = dict(runs=['6106D'], bias='orig',
                   superbias='orig', outdir='test_out', plot='png')
SUMMARY_OPTIONS = dict(dataset='tests/test', bias='orig',
                       superbias='orig', outdir='test_out', plot='png')

def test_fe55_file_utils():
    """Test the fe55.file_utils module"""
    fe55_files_6106 = get_fe55_files_run('6106D')
    assert len(fe55_files_6106) == 1
    assert 'RTM-004' in fe55_files_6106
    assert len(fe55_files_6106['RTM-004']) == 9
    assert len(fe55_files_6106['RTM-004']['S00']) == 1
    assert 'FE55' in fe55_files_6106['RTM-004']['S00']
    assert len(fe55_files_6106['RTM-004']['S00']['FE55']) == 10

    fe55_files_6545 = get_fe55_files_run('6545D')
    assert len(fe55_files_6545) == 2
    assert 'R10' in fe55_files_6545
    assert len(fe55_files_6545['R10']) == 9
    assert len(fe55_files_6545['R10']['S00']) == 1
    assert 'FE55' in fe55_files_6545['R10']['S00']
    #FIXME
    #assert len(fe55_files_6545['R10']['S00']['FE55']) == 35


def test_fe55_butler_utils():
    """Test the fe55.butler_utils module"""
    return

def test_fe55_gain_stats():
    """Test the Fe55GainStatsTask"""
    task = fe55.Fe55GainStatsTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_fe55_gain_sum():
    """Test the Fe55GainSummaryTask"""
    task = fe55.Fe55GainSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
