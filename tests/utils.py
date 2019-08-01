# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Utilities for lsst.eo_utils unit tests"""

from __future__ import absolute_import, division, print_function

import os
from astropy.tests.helper import pytest

__all__ = ['requires_file', 'RUN_TASKS']

DATA_OPTIONS_TS8_GLOB = dict(teststand='ts8', data_source='glob')
DATA_OPTIONS_BOT_GLOB = dict(teststand='bot_etu', data_source='glob')
DATA_OPTIONS_TS8_BUTLER = dict(teststand='ts8', data_source='butler')
DATA_OPTIONS_BOT_BUTLER = dict(teststand='bot_etu', data_source='butler')

RUN_TASKS = True
if os.environ.get('EO_TEST_NO_RUN_TASKS', False):
    RUN_TASKS = False

RUN_OPTIONS = dict(runs=['6106D'], outdir='test_out', plot='png')
RUN_OPTIONS_NOPLOT = dict(runs=['6106D'], outdir='test_out')
SUMMARY_OPTIONS = dict(dataset='tests/test', outdir='test_out', plot='png')

def requires_file(filepath):
    """Skip test if required file is missing"""
    skip_it = bool(not os.path.isfile(filepath))
    return pytest.mark.skipif(skip_it,
                              reason='File %s does not exist.' % filepath)


def assert_data_dict(the_dict, raft_name, key_name, size_tuple):
    """Check that a dictionary matches the expected size"""
    dict_size = [0, 0, 0, 0]
    try:
        dict_size[0] = len(the_dict)
        assert dict_size[0] == size_tuple[0]
        assert raft_name in the_dict
        dict_size[1] = len(the_dict[raft_name])
        assert dict_size[1] == size_tuple[1]
        dict_size[2] = len(the_dict[raft_name]['S00'])
        assert dict_size[2] == size_tuple[2]
        assert key_name in the_dict[raft_name]['S00']
        dict_size[3] = len(the_dict[raft_name]['S00'][key_name])
        assert dict_size[3] == size_tuple[3]
    except AssertionError:
        raise ValueError("%s != %s\n" % (str(dict_size), str(size_tuple)))
