# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.ppump module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.butler_utils import get_butler_by_repo
from lsst.eo_utils import ppump

from .utils import DATA_OPTIONS_TS8_GLOB, DATA_OPTIONS_BOT_GLOB,\
    DATA_OPTIONS_TS8_BUTLER, DATA_OPTIONS_BOT_BUTLER,\
    RUN_TASKS, RUN_OPTIONS


def test_ppump_file_utils():
    """Test the ppump.file_utils module"""
    ppump_files_6106 = ppump.PpumpAnalysisTask.get_data(None, '6106D',
                                                        **DATA_OPTIONS_TS8_GLOB)
    assert len(ppump_files_6106) == 1
    assert 'RTM-004' in ppump_files_6106
    assert len(ppump_files_6106['RTM-004']) == 9
    assert len(ppump_files_6106['RTM-004']['S00']) == 1
    assert 'PPUMP' in ppump_files_6106['RTM-004']['S00']
    assert len(ppump_files_6106['RTM-004']['S00']['PPUMP']) == 2

    ppump_files_6545 = ppump.PpumpAnalysisTask.get_data(None, '6545D',
                                                        **DATA_OPTIONS_BOT_GLOB)
    assert len(ppump_files_6545) == 2
    assert 'R10' in ppump_files_6545
    assert len(ppump_files_6545['R10']) == 9
    assert len(ppump_files_6545['R10']['S00']) == 1
    assert 'PPUMP' in ppump_files_6545['R10']['S00']
    #FIXME
    #assert len(ppump_files_6545['R10']['S00']['PPUMP']) == 2


def test_ppump_butler_utils():
    """Test the ppump.butler_utils module"""
    ts8_butler = get_butler_by_repo('ts8')
    bot_butler = get_butler_by_repo('bot')

    ppump_files_6106 = ppump.PpumpAnalysisTask.get_data(ts8_butler, '6106D',
                                                        **DATA_OPTIONS_TS8_BUTLER)
    assert len(ppump_files_6106) == 1
    assert 'RTM-004' in ppump_files_6106
    assert len(ppump_files_6106['RTM-004']) == 9
    assert len(ppump_files_6106['RTM-004']['S00']) == 1
    assert 'PPUMP' in ppump_files_6106['RTM-004']['S00']
    #FIXME
    #assert len(ppump_files_6106['RTM-004']['S00']['PPUMP']) == 2

    #FIXME
    #ppump_files_6545 = ppump.PpumpAnalysisTask.get_data(bot_butler, '6545D',
    #                                                    **DATA_OPTIONS_BOT_BUTLER)
    #assert len(ppump_files_6545) == 2
    #assert 'R10' in ppump_files_6545
    #assert len(ppump_files_6545['R10']) == 9
    #assert len(ppump_files_6545['R10']['S00']) == 1
    #assert 'PPUMP' in ppump_files_6545['R10']['S00']
    #assert len(ppump_files_6545['R10']['S00']['PPUMP']) == 2

def test_ppump_traps():
    """Test the TrapTask"""
    task = ppump.TrapTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS)
