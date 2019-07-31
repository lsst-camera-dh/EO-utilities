# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.sflat module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.butler_utils import get_butler_by_repo
from lsst.eo_utils import sflat

from .utils import  DATA_OPTIONS_TS8_GLOB, DATA_OPTIONS_BOT_GLOB,\
    DATA_OPTIONS_TS8_BUTLER, DATA_OPTIONS_BOT_BUTLER,\
    RUN_TASKS, RUN_OPTIONS, RUN_OPTIONS_NOPLOT


def test_sflat_file_utils():
    """Test the sflat.file_utils module"""
    sflat_files_6106 = sflat.SflatAnalysisTask.get_data(None, '6106D',
                                                        **DATA_OPTIONS_TS8_GLOB)
    assert len(sflat_files_6106) == 1
    assert 'RTM-004' in sflat_files_6106
    assert len(sflat_files_6106['RTM-004']) == 9
    assert len(sflat_files_6106['RTM-004']['S00']) == 1
    assert 'SFLAT' in sflat_files_6106['RTM-004']['S00']
    assert len(sflat_files_6106['RTM-004']['S00']['SFLAT']) == 72

    sflat_files_6545 = sflat.SflatAnalysisTask.get_data(None, '6545D',
                                                        **DATA_OPTIONS_BOT_GLOB)
    assert len(sflat_files_6545) == 2
    assert 'R10' in sflat_files_6545
    assert len(sflat_files_6545['R10']) == 9
    assert len(sflat_files_6545['R10']['S00']) == 1
    assert 'SFLAT' in sflat_files_6545['R10']['S00']
    assert len(sflat_files_6545['R10']['S00']['SFLAT']) == 35


def test_sflat_butler_utils():
    """Test the sflat.butler_utils module"""
    ts8_butler = get_butler_by_repo('ts8')
    bot_butler = get_butler_by_repo('bot')
    #FIXME
    #sflat_files_6106 = sflat.SflatAnalysisTask.get_data(ts8_butler, '6106D',
    #                                                    **DATA_OPTIONS_TS8_BUTLER)
    #assert len(sflat_files_6106) == 1
    #assert 'RTM-004' in sflat_files_6106
    #assert len(sflat_files_6106['RTM-004']) == 9
    #assert len(sflat_files_6106['RTM-004']['S00']) == 1
    #assert 'SFLAT' in sflat_files_6106['RTM-004']['S00']
    #assert len(sflat_files_6106['RTM-004']['S00']['SFLAT']) == 72

    #sflat_files_6545 = sflat.SflatAnalysisTask.get_data(bot_butler, '6545D',
    #                                                    **DATA_OPTIONS_BOT_BUTLER)
    #assert len(sflat_files_6545) == 2
    #assert 'R10' in sflat_files_6545
    #assert len(sflat_files_6545['R10']) == 9
    #assert len(sflat_files_6545['R10']['S00']) == 1
    #assert 'SFLAT' in sflat_files_6545['R10']['S00']
    #assert len(sflat_files_6545['R10']['S00']['SFLAT']) == 35


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
