# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Utilities for lsst.eo_utils unit tests"""

from __future__ import absolute_import, division, print_function

import os
from astropy.tests.helper import pytest

__all__ = ['requires_file', 'RUN_TASKS']

RUN_TASKS = True

def requires_file(filepath):
    "Skip test if required file is missing"""
    skip_it = bool(not os.path.isfile(filepath))
    return pytest.mark.skipif(skip_it,
                              reason='File %s does not exist.' % filepath)
