# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.flat module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import flat
from lsst.eo_utils.flat.file_utils import get_flat_files_run

from .utils import RUN_TASKS

RUN_OPTIONS = dict(runs=['6106D'], bias='spline',
                   superbias='spline', outdir='test_out', plot='png')
SUMMARY_OPTIONS = dict(dataset='tests/test', bias='spline',
                       superbias='spline', outdir='test_out', plot='png')


def test_flat_file_utils():
    """Test the flat.file_utils module"""
    flat_files_6106 = get_flat_files_run('6106D')
    assert len(flat_files_6106) == 1
    assert 'RTM-004' in flat_files_6106
    assert len(flat_files_6106['RTM-004']) == 9
    assert len(flat_files_6106['RTM-004']['S00']) == 2
    assert 'FLAT1' in flat_files_6106['RTM-004']['S00']
    assert len(flat_files_6106['RTM-004']['S00']['FLAT1']) == 43

    flat_files_6545 = get_flat_files_run('6545D')
    assert len(flat_files_6545) == 2
    assert 'R10' in flat_files_6545
    assert len(flat_files_6545['R10']) == 9
    assert len(flat_files_6545['R10']['S00']) == 2
    assert 'FLAT1' in flat_files_6545['R10']['S00']
    assert len(flat_files_6545['R10']['S00']['FLAT1']) == 43

def test_flat_butler_utils():
    """Test the flat.butler_utils module"""
    return

def test_flat_oscan():
    """Test the FlatOverscanTask"""
    task = flat.FlatOverscanTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_flat_pair():
    """Test the FlatPairTask"""
    task = flat.FlatPairTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_flat_linearity():
    """Test the FlatLinearityTask"""
    task = flat.FlatLinearityTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_flat_bf():
    """Test the BFTask"""
    task = flat.BFTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_flat_ptc():
    """Test the PTCTask"""
    task = flat.PTCTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_flat_ptc_sum():
    """Test the PTCSummaryTask"""
    task = flat.PTCSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
