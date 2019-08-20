# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.fe55 module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.butler_utils import get_butler_by_repo
from lsst.eo_utils import fe55

from .utils import assert_data_dict, requires_site,\
    DATA_OPTIONS_TS8_GLOB, DATA_OPTIONS_BOT_GLOB,\
    DATA_OPTIONS_TS8_BUTLER, DATA_OPTIONS_BOT_BUTLER,\
    RUN_TASKS, RUN_OPTIONS, SUMMARY_OPTIONS

@requires_site('slac')
def test_fe55_file_utils():
    """Test the fe55.file_utils module"""
    fe55_files_6106 = fe55.Fe55AnalysisTask.get_data(None, '6106D',
                                                     **DATA_OPTIONS_TS8_GLOB)
    assert_data_dict(fe55_files_6106, 'RTM-004', 'FE55', (1, 9, 1, 10))

    fe55_files_6545 = fe55.Fe55AnalysisTask.get_data(None, '6545D',
                                                     **DATA_OPTIONS_BOT_GLOB)
    assert_data_dict(fe55_files_6545, 'R10', 'FE55', (2, 9, 1, 5))


def test_fe55_butler_utils():
    """Test the fe55.butler_utils module"""
    ts8_butler = get_butler_by_repo('ts8')
    bot_butler = get_butler_by_repo('bot')
    fe55_files_6106 = fe55.Fe55AnalysisTask.get_data(ts8_butler, '6106D',
                                                     **DATA_OPTIONS_TS8_BUTLER)
    assert_data_dict(fe55_files_6106, 'RTM-004', 'FE55', (1, 9, 1, 5))

    fe55_files_6545 = fe55.Fe55AnalysisTask.get_data(bot_butler, '6545D',
                                                     **DATA_OPTIONS_BOT_BUTLER)
    assert_data_dict(fe55_files_6545, 'R10', 'FE55', (2, 9, 1, 5))


@requires_site('slac')
def test_fe55_gain_stats():
    """Test the Fe55GainStatsTask"""
    task = fe55.Fe55GainStatsTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

@requires_site('slac')
def test_fe55_gain_sum():
    """Test the Fe55GainSummaryTask"""
    task = fe55.Fe55GainSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)
