# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.bias module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import bias
from lsst.eo_utils.bias.file_utils import get_bias_files_run

from .utils import RUN_TASKS, RUN_OPTIONS, RUN_OPTIONS_NOPLOT, SUMMARY_OPTIONS

def test_bias_file_utils():
    """Test the bias.file_utils module"""
    bias_files_6106 = get_bias_files_run('6106D')
    assert len(bias_files_6106) == 1
    assert 'RTM-004' in bias_files_6106
    assert len(bias_files_6106['RTM-004']) == 9
    assert len(bias_files_6106['RTM-004']['S00']) == 1
    assert 'BIAS' in bias_files_6106['RTM-004']['S00']
    assert len(bias_files_6106['RTM-004']['S00']['BIAS']) == 124

    bias_files_6545 = get_bias_files_run('6545D')
    assert len(bias_files_6545) == 2
    assert 'R10' in bias_files_6545
    assert len(bias_files_6545['R10']) == 9
    assert len(bias_files_6545['R10']['S00']) == 1
    assert 'BIAS' in bias_files_6545['R10']['S00']
    assert len(bias_files_6545['R10']['S00']['BIAS']) == 159


def test_bias_butler_utils():
    """Test the bias.butler_utils module"""
    return

def test_superbias():
    """Test the SuperbiasTask"""
    task = bias.SuperbiasTask()
    if RUN_TASKS:
        task.run(nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_superbias_raft():
    """Test the SuperbiasRaftTask"""
    task = bias.SuperbiasRaftTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS_NOPLOT)

def test_bias_fft():
    """Test the BiasFFTTask"""
    task = bias.BiasFFTTask()
    if RUN_TASKS:
        task.run(nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_bias_fft_stats():
    """Test the BiasFFTStatsTask"""
    task = bias.BiasFFTStatsTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS_NOPLOT)

def test_bias_fft_sum():
    """Test the BiasFFTSummaryTask"""
    task = bias.BiasFFTSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)

def test_superbias_fft():
    """Test the SuperbiasFFTTask"""
    task = bias.SuperbiasFFTTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS)

def test_bias_struct():
    """Test the BiasStructTask"""
    task = bias.BiasStructTask()
    if RUN_TASKS:
        task.run(nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_superbias_struct():
    """Test theSuperbiasStructTask """
    task = bias.SuperbiasStructTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS)

def test_bias_v_row():
    """Test the BiasVRowTask"""
    task = bias.BiasVRowTask()
    if RUN_TASKS:
        task.run(nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_correl_wrt_oscan():
    """Test the CorrelWRTOscanTask"""
    task = bias.CorrelWRTOscanTask()
    if RUN_TASKS:
        task.run(nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_correl_wrt_oscan_stats():
    """Test the CorrelWRTOscanStatsTask"""
    task = bias.CorrelWRTOscanStatsTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_correl_wrt_oscan_sum():
    """Test the CorrelWRTOscanSummaryTask"""
    task = bias.CorrelWRTOscanSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)

def test_oscan_amp_stack():
    """Test the OscanAmpStackTask"""
    task = bias.OscanAmpStackTask()
    if RUN_TASKS:
        task.run(nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_oscan_amp_stack_stats():
    """Test the OscanAmpStackStatsTask"""
    task = bias.OscanAmpStackStatsTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_oscan_amp_stack_sum():
    """Test the OscanAmpStackSummaryTask"""
    task = bias.OscanAmpStackSummaryTask()
    if RUN_TASKS:
        task.run(**SUMMARY_OPTIONS)

def test_oscan_correl():
    """Test the OscanCorrelTask"""
    task = bias.OscanCorrelTask()
    if RUN_TASKS:
        task.run(superbias=None, **RUN_OPTIONS)

def test_superbias_stdev():
    """Test the SuperbiasTask in stdevclip mode"""
    task = bias.SuperbiasTask()
    if RUN_TASKS:
        task.run(stat='stdevclip', nfiles=2, slots=['S00'], **RUN_OPTIONS)

def test_superbias_stdev_stats():
    """Test the SuperbiasStatsTask"""
    task = bias.SuperbiasStatsTask()
    if RUN_TASKS:
        task.run(stat='stdevclip', slots=['S00'], **RUN_OPTIONS)

def test_superbias_stdev_sum():
    """Test the SuperbiasSummaryTask"""
    task = bias.SuperbiasSummaryTask()
    if RUN_TASKS:
        task.run(stat='stdevclip', **SUMMARY_OPTIONS)
