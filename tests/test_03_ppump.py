# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.ppump module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.butler_utils import get_butler_by_repo
from lsst.eo_utils import ppump

from .utils import assert_data_dict, requires_site,\
    DATA_OPTIONS_TS8_GLOB,\
    DATA_OPTIONS_TS8_BUTLER,\
    RUN_TASKS, RUN_OPTIONS


@requires_site('slac')
def test_ppump_file_utils():
    """Test the ppump.file_utils module"""
    ppump_files_6106 = ppump.PpumpAnalysisTask.get_data(None, '6106D',
                                                        **DATA_OPTIONS_TS8_GLOB)
    assert_data_dict(ppump_files_6106, 'RTM-004', 'PPUMP', (1, 9, 1, 2))
    #Pocket pumping is not included in BOT Tests


def test_ppump_butler_utils():
    """Test the ppump.butler_utils module"""
    ts8_butler = get_butler_by_repo('ts8')

    ppump_files_6106 = ppump.PpumpAnalysisTask.get_data(ts8_butler, '6106D',
                                                        **DATA_OPTIONS_TS8_BUTLER)
    assert_data_dict(ppump_files_6106, 'RTM-004', 'PPUMP', (1, 9, 1, 2))
    #Pocket pumping is not included in BOT Tests


def test_ppump_traps():
    """Test the TrapTask"""
    task = ppump.TrapTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS)
