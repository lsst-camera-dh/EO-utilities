# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.sflat module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import sflat
from lsst.eo_utils.sflat.file_utils import get_sflat_files_run

from .utils import RUN_TASKS, RUN_OPTIONS, RUN_OPTIONS_NOPLOT


def test_sflat_file_utils():
    """Test the sflat.file_utils module"""
    sflat_files_6106 = get_sflat_files_run('6106D')
    assert len(sflat_files_6106) == 1
    assert 'RTM-004' in sflat_files_6106
    assert len(sflat_files_6106['RTM-004']) == 9
    assert len(sflat_files_6106['RTM-004']['S00']) == 1
    assert 'SFLAT' in sflat_files_6106['RTM-004']['S00']
    assert len(sflat_files_6106['RTM-004']['S00']['SFLAT']) == 72

    sflat_files_6545 = get_sflat_files_run('6545D')
    assert len(sflat_files_6545) == 2
    assert 'R10' in sflat_files_6545
    assert len(sflat_files_6545['R10']) == 9
    assert len(sflat_files_6545['R10']['S00']) == 1
    assert 'SFLAT' in sflat_files_6545['R10']['S00']
    assert len(sflat_files_6545['R10']['S00']['SFLAT']) == 35


def test_sflat_butler_utils():
    """Test the sflat.butler_utils module"""
    return

def test_superflat():
    """Test the SuperflatTask"""
    task = sflat.SuperflatTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS)

def test_superflat_raft():
    """Test the SuperflatRaftTask"""
    task = sflat.SuperflatRaftTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS_NOPLOT)

def test_sflat_ratio():
    """Test the SflatRatioTask"""
    task = sflat.SflatRatioTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS_NOPLOT)

def test_sflat_cte():
    """Test the CTETask"""
    task = sflat.CTETask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS_NOPLOT)
