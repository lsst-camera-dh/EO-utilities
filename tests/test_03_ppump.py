# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.ppump module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import ppump
from lsst.eo_utils.ppump.file_utils import get_ppump_files_run

from .utils import RUN_TASKS

RUN_OPTIONS = dict(runs=['6106D'], bias='spline', superbias='spline', outdir='test_out', plot='png')
SUMMARY_OPTIONS = dict(dataset='test', bias='spline',
                       superbias='spline', outdir='test_out', plot='png')

def test_ppump_file_utils():
    """Test the ppump.file_utils module"""
    ppump_files_6106 = get_ppump_files_run('6106D')
    assert len(ppump_files_6106) == 1
    assert 'RTM-004' in ppump_files_6106
    assert len(ppump_files_6106['RTM-004']) == 9
    assert len(ppump_files_6106['RTM-004']['S00']) == 1
    assert 'PPUMP' in ppump_files_6106['RTM-004']['S00']
    assert len(ppump_files_6106['RTM-004']['S00']['PPUMP']) == 2

    ppump_files_6545 = get_ppump_files_run('6545D')
    assert len(ppump_files_6545) == 2
    assert 'R10' in ppump_files_6545
    assert len(ppump_files_6545['R10']) == 9
    assert len(ppump_files_6545['R10']['S00']) == 1
    assert 'PPUMP' in ppump_files_6545['R10']['S00']
    #FIXME
    #assert len(ppump_files_6545['R10']['S00']['PPUMP']) == 2


def test_ppump_butler_utils():
    """Test the ppump.butler_utils module"""
    return

def test_ppump_traps():
    """Test the TrapTask"""
    task = ppump.TrapTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)
