# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.qe module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import qe
from lsst.eo_utils.qe.file_utils import get_qe_files_run

from .utils import RUN_TASKS

RUN_OPTIONS = dict(runs=['6106D'], bias='spline',
                   superbias='spline', outdir='test_out', plot='png')
SUMMARY_OPTIONS = dict(dataset='test', bias='spline',
                       superbias='spline', outdir='test_out', plot='png')


def test_qe_file_utils():
    """Test the qe.file_utils module"""
    qe_files_6106 = get_qe_files_run('6106D')
    assert len(qe_files_6106) == 1
    assert 'RTM-004' in qe_files_6106
    assert len(qe_files_6106['RTM-004']) == 9
    assert len(qe_files_6106['RTM-004']['S00']) == 2
    assert 'LAMBDA' in qe_files_6106['RTM-004']['S00']
    assert len(qe_files_6106['RTM-004']['S00']['LAMBDA']) == 36

    qe_files_6545 = get_qe_files_run('6545D')
    assert len(qe_files_6545) == 2
    assert 'R10' in qe_files_6545
    assert len(qe_files_6545['R10']) == 9
    assert len(qe_files_6545['R10']['S00']) == 2
    assert 'LAMBDA' in qe_files_6545['R10']['S00']
    #FIXME
    #assert(len(qe_files_6545['R10']['S00']['LAMBDA']) == 10)


def test_qe_butler_utils():
    """Test the qe.butler_utils module"""
    return

def test_qe_median():
    """Test the QEMedianTask"""
    task = qe.QEMedianTask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)

def test_qe_task():
    """Test the QETask"""
    task = qe.QETask()
    if RUN_TASKS:
        task.run(**RUN_OPTIONS)
