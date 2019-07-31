# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.dark module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.butler_utils import get_butler_by_repo
from lsst.eo_utils import dark


from .utils import DATA_OPTIONS_TS8_GLOB, DATA_OPTIONS_BOT_GLOB,\
    DATA_OPTIONS_TS8_BUTLER, DATA_OPTIONS_BOT_BUTLER,\
    RUN_TASKS, RUN_OPTIONS, RUN_OPTIONS_NOPLOT, SUMMARY_OPTIONS

def test_dark_file_utils():
    """Test the dark.file_utils module"""
    dark_files_6106 = dark.DarkAnalysisTask.get_data(None, '6106D',
                                                     **DATA_OPTIONS_TS8_GLOB)
    assert len(dark_files_6106) == 1
    assert 'RTM-004' in dark_files_6106
    assert len(dark_files_6106['RTM-004']) == 9
    assert len(dark_files_6106['RTM-004']['S00']) == 1
    assert 'DARK' in dark_files_6106['RTM-004']['S00']
    assert len(dark_files_6106['RTM-004']['S00']['DARK']) == 5

    dark_files_6545 = dark.DarkAnalysisTask.get_data(None, '6545D',
                                                     **DATA_OPTIONS_BOT_GLOB)
    assert len(dark_files_6545) == 2
    assert 'R10' in dark_files_6545
    assert len(dark_files_6545['R10']) == 9
    assert len(dark_files_6545['R10']['S00']) == 1
    assert 'DARK' in dark_files_6545['R10']['S00']
    assert len(dark_files_6545['R10']['S00']['DARK']) == 5


def test_dark_butler_utils():
    """Test the dark.butler_utils module"""
    ts8_butler = get_butler_by_repo('ts8')
    bot_butler = get_butler_by_repo('bot')

    dark_files_6106 = dark.DarkAnalysisTask.get_data(ts8_butler, '6106D',
                                                     **DATA_OPTIONS_TS8_BUTLER)
    assert len(dark_files_6106) == 1
    assert 'RTM-004' in dark_files_6106
    assert len(dark_files_6106['RTM-004']) == 9
    assert len(dark_files_6106['RTM-004']['S00']) == 1
    assert 'DARK' in dark_files_6106['RTM-004']['S00']
    assert len(dark_files_6106['RTM-004']['S00']['DARK']) == 5

    dark_files_6545 = dark.DarkAnalysisTask.get_data(bot_butler, '6545D',
                                                     **DATA_OPTIONS_BOT_BUTLER)
    assert len(dark_files_6545) == 2
    assert 'R10' in dark_files_6545
    assert len(dark_files_6545['R10']) == 9
    assert len(dark_files_6545['R10']['S00']) == 1
    assert 'DARK' in dark_files_6545['R10']['S00']
    assert len(dark_files_6545['R10']['S00']['DARK']) == 5

def test_superdark():
    """Test the SuperdarkTask"""
    task = dark.SuperdarkTask()
    if RUN_TASKS:
        task.run(nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_superdark_raft():
    """Test the SuperdarkRaftTask"""
    task = dark.SuperdarkRaftTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS_NOPLOT)

def test_dark_current():
    """Test the DarkCurrentTask"""
    task = dark.DarkCurrentTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS_NOPLOT)

def test_dark_current_sum():
    """Test the DarkCurrentSummaryTask"""
    task = dark.DarkCurrentSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
