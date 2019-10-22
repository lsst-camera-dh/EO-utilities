# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.qe module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils.base.defaults import SITE
from lsst.eo_utils.base.butler_utils import get_butler_by_repo
from lsst.eo_utils import qe

from .utils import assert_data_dict, requires_site,\
    DATA_OPTIONS_TS8_GLOB, DATA_OPTIONS_BOT_GLOB,\
    DATA_OPTIONS_TS8_BUTLER, DATA_OPTIONS_BOT_BUTLER,\
    RUN_TASKS, RUN_OPTIONS

@requires_site('slac')
def test_qe_file_utils():
    """Test the qe.file_utils module"""
    qe_files_6106 = qe.QeAnalysisTask.get_data(None, '6106D',
                                               **DATA_OPTIONS_TS8_GLOB)
    assert_data_dict(qe_files_6106, 'RTM-004', 'LAMBDA', (1, 9, 1, 36))

    qe_files_6545 = qe.QeAnalysisTask.get_data(None, '6545D',
                                               **DATA_OPTIONS_BOT_GLOB)
    assert_data_dict(qe_files_6545, 'R10', 'LAMBDA', (2, 9, 1, 12))


def test_qe_butler_utils():
    """Test the qe.butler_utils module"""
    ts8_butler = get_butler_by_repo('ts8')
    bot_butler = get_butler_by_repo('bot')

    qe_files_6106 = qe.QeAnalysisTask.get_data(ts8_butler, '6106D',
                                               **DATA_OPTIONS_TS8_BUTLER)
    assert_data_dict(qe_files_6106, 'RTM-004', 'LAMBDA', (1, 9, 1, 36))

    qe_files_6545 = qe.QeAnalysisTask.get_data(bot_butler, '6545D',
                                               **DATA_OPTIONS_BOT_BUTLER)
    assert_data_dict(qe_files_6545, 'R10', 'LAMBDA', (2, 9, 1, 12))


def test_qe_median():
    """Test the QEMedianTask"""
    task = qe.QEMedianTask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS)


@requires_site('slac')
def test_qe_task():
    """Test the QETask"""
    task = qe.QETask()
    if RUN_TASKS:
        task.run(slots=['S00'], **RUN_OPTIONS)
