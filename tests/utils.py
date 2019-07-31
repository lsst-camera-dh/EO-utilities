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
RUN_OPTIONS = dict(runs=['6106D'], outdir='test_out', plot='png')
RUN_OPTIONS_NOPLOT = dict(runs=['6106D'], outdir='test_out')
SUMMARY_OPTIONS = dict(dataset='tests/test', outdir='test_out', plot='png')

def requires_file(filepath):
    "Skip test if required file is missing"""
    skip_it = bool(not os.path.isfile(filepath))
    return pytest.mark.skipif(skip_it,
                              reason='File %s does not exist.' % filepath)
