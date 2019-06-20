# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.base module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.file_utils import merge_file_dicts,\
    get_files_for_run, get_raft_names_dc, read_raft_ccd_map,\
    read_runlist

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.config_utils import EOUtilOptions


def test_config_utils():
    """Test the config_utils module"""
    opt_object = EOUtilOptions()
    par_dict = opt_object.toDict()
    for key, val in par_dict.items():
        cloned = EOUtilOptions.clone_param(key)
        assert isinstance(val, cloned.dtype) or val is None

def test_stat_utils():
    """Test the stats_utils module"""
    return


def test_file_utils_get_ts8():
    """Test the file_utils module"""
    bias_files = get_files_for_run('6106D',
                                   imagetype='BIAS',
                                   testtypes=['dark_raft_acq'],
                                   outkey='BIAS')
    dark_files = get_files_for_run('6106D',
                                   imagetype='DARK_DARK',
                                   testtypes=['dark_raft_acq'],
                                   outkey='DARK')
    files = merge_file_dicts(bias_files, dark_files)
    assert len(files) == 1
    assert 'RTM-004' in files
    assert len(files['RTM-004']) == 9
    assert len(files['RTM-004']['S00']) == 2
    assert 'BIAS' in files['RTM-004']['S00']
    assert 'DARK' in files['RTM-004']['S00']
    assert len(files['RTM-004']['S00']['BIAS']) == 5
    assert len(files['RTM-004']['S00']['DARK']) == 5


def test_file_utils_get_bot():
    """Test the file_utils module"""
    bias_files = get_files_for_run('6545D',
                                   imagetype='BIAS',
                                   testtypes=['DARK'],
                                   outkey='BIAS')
    dark_files = get_files_for_run('6545D',
                                   imagetype='DARK',
                                   testtypes=['DARK'],
                                   outkey='DARK')
    files = merge_file_dicts(bias_files, dark_files)
    assert len(files) == 2
    assert 'R10' in files
    assert len(files['R10']) == 9
    assert len(files['R10']['S00']) == 2
    assert 'BIAS' in files['R10']['S00']
    assert 'DARK' in files['R10']['S00']
    assert len(files['R10']['S00']['BIAS']) == 25
    assert len(files['R10']['S00']['DARK']) == 5


def test_file_utils_get_names_dc():
    """Test the file_utils module"""
    rafts_6106 = get_raft_names_dc('6106D')
    assert len(rafts_6106) == 1
    assert rafts_6106[0] == 'RTM-004'

    rafts_6545 = get_raft_names_dc('6545D')
    assert len(rafts_6545) == 2
    assert rafts_6545[0] == 'R10'
    assert rafts_6545[1] == 'R22'


def test_file_utils_read_raft_map():
    """Test the file_utils module"""
    ccdmap = read_raft_ccd_map('tests/test_ts8_mapping.yaml')
    assert len(ccdmap['RTM-004']) == 9

def test_file_utils_read_runlist():
    """Test the file_utils module"""
    runs = read_runlist('tests/test_runs.txt')
    assert len(runs) == 2
    assert len(runs[0]) == 2
    assert len(runs[1]) == 2

def test_butler_utils():
    """Test the butler_utils module"""
    return

def test_data_utils():
    """Test the data_utils module"""
    tab_dict = TableDict()
    assert tab_dict is not None

def test_plot_utils():
    """Test the plot_utils module"""
    fig_dict = FigureDict()
    assert fig_dict is not None
