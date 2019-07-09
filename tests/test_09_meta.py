# Licensed under a 3-clause BSD style license - see LICENSE.rst
"Unit tests for lsst.eo_utils.qe module"""

from __future__ import absolute_import, division, print_function

from lsst.eo_utils import meta

#from .utils import RUN_TASKS

#RUN_OPTIONS = dict(runs=['6106D'], bias='spline',
#                   superbias='spline', outdir='test_out', plot='png')
#SUMMARY_OPTIONS = dict(dataset='tests/test', bias='spline',
#                       superbias='spline', outdir='test_out', plot='png')


def test_meta_calib_stack():
    """Test the CalibStackTask"""
    task = meta.CalibStackTask()
    assert task

def test_meta_defect_analysis():
    """Test the DefectAnalysisTask"""
    task = meta.DefectAnalysisTask()
    assert task

def test_meta_slot_analysis():
    """Test the SlotAnalysisTask"""
    task = meta.SlotAnalysisTask()
    assert task

def test_meta_slot_table_analysis():
    """Test the SlotTableAnalysisTask"""
    task = meta.SlotTableAnalysisTask()
    assert task

def test_meta_raft_analysis():
    """Test the RaftAnalysisTask"""
    task = meta.RaftAnalysisTask()
    assert task

def test_meta_summary_analysis():
    """Test the SummaryAnalysisTask"""
    task = meta.SummaryAnalysisTask()
    assert task
