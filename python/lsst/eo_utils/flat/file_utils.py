#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import DATACAT_TS8_TEST_TYPES, DATACAT_BOT_TEST_TYPES

from lsst.eo_utils.base.config_utils import copy_dict

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    get_slot_file_basename, get_raft_file_basename, get_summary_file_basename



RAFT_FLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='flat', run_num=None, suffix='')
RAFT_FLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='flat', run_num=None, suffix='')
SLOT_FLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='flat', run_num=None, slot=None, suffix='')
SLOT_FLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='flat', run_num=None, slot=None, suffix='')

RAFT_SFLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                     testType='superflat', run_num=None, suffix='')
RAFT_SFLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                    testType='superflat', run_num=None, suffix='')
SLOT_SFLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                     testType='superflat', run_num=None, slot=None, suffix='')
SLOT_SFLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                    testType='superflat', run_num=None, slot=None, suffix='')

FLAT_SUMMARY_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables',
                                       testType='flat', dataset=None, suffix='')
FLAT_SUMMARY_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots',
                                      testType='flat', dataset=None, suffix='')
SFLAT_SUMMARY_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables',
                                        testType='superflat', dataset=None, suffix='')
SFLAT_SUMMARY_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots',
                                       testType='superflat', dataset=None, suffix='')


def raft_flat_tablename(**kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/tables/{raft}/flat/{raft}-{run_num}-RFT_b-{flat_type}_s-{superflat_type}{suffix}

    @param kwargs:          Passed to get_flat_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_FLAT_TABLENAME_DEFAULTS)
    outbase = get_raft_file_basename(**kwcopy)

    return str(outbase)

def raft_flat_plotname(**kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/plots/{raft}/flat/{raft}-{run_num}-{slot}_b-{flat_type}_s-{superflat_type}{suffix}

    @param kwargs:          Passed to get_flat_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_FLAT_PLOTNAME_DEFAULTS)
    outbase = get_raft_file_basename(**kwcopy)
    return str(outbase)



def slot_flat_tablename(**kwargs):
    """Return the filename for a plot made from a flat file

    The format is {outdir}/tables/{raft}/flat/{raft}-{run_num}-{slot}_b-{flat_type}_s-{superflat_type}

    @param kwargs           Passed to get_flat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_FLAT_TABLENAME_DEFAULTS)
    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_flat_plotname(**kwargs):
    """Return the filename for a plot made from a flat file

    The format is {outdir}/plots/{raft}/flat/{raft}-{run_num}-{slot}_b-{flat_type}_s-{superflat_type}

    @param kwargs           Passed to get_flat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_FLAT_PLOTNAME_DEFAULTS)
    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_superflat_tablename(**kwargs):
    """Return the filename for a plot made from a superflat file

    The format is {outdir}/tables/{raft}/superflat/{raft}-{run_num}-{slot}_b-{superflat_type}

    @param kwargs           Passed to get_superflat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_SFLAT_TABLENAME_DEFAULTS)
    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_superflat_plotname(**kwargs):
    """Return the filename for a plot made from a superflat file

    @param kwargs           Passed to get_superflat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_SFLAT_PLOTNAME_DEFAULTS)
    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def raft_superflat_tablename(**kwargs):
    """Return the filename for a plot made from a superflat file

    The format is {outdir}/tables/{raft}/superflat/{raft}-{run_num}-{slot}_b-{superflat_type}

    @param kwargs           Passed to get_superflat_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_SFLAT_TABLENAME_DEFAULTS)
    outpath = get_raft_file_basename(**kwcopy)
    return str(outpath)

def raft_superflat_plotname(**kwargs):
    """Return the filename for a plot made from a superflat file

    The format is {outdir}/plots/{raft}/superflat/{raft}-{run_num}-{slot}_b-{superflat_type}

    @param kwargs           Passed to get_superflat_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_SFLAT_PLOTNAME_DEFAULTS)
    outpath = get_raft_file_basename(**kwcopy)
    return str(outpath)


def flat_summary_tablename(**kwargs):
    """Return the filename for a summary table file

    The format is {outdir}/tables/summary/flat/{dataset}{suffix}

    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, FLAT_SUMMARY_TABLENAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)
    return str(outpath)

def flat_summary_plotname(**kwargs):
    """Return the filename for a summary plot file

    The format is {outdir}/plots/summary/flat/{dataset}{suffix}

    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, FLAT_SUMMARY_PLOTNAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)
    return str(outpath)

def superflat_summary_tablename(**kwargs):
    """Return the filename for a summary table file

    The format is {outdir}/tables/summary/flat/{dataset}{suffix}

    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SFLAT_SUMMARY_TABLENAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)
    return str(outpath)


def superflat_summary_plotname(**kwargs):
    """Return the filename for a summary plot file

    The format is {outdir}/plots/summary/flat/{dataset}{suffix}

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SFLAT_SUMMARY_PLOTNAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)

    return str(outpath)


def get_flat_files_run(run_id, **kwargs):
    """Get a set of flat and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)
    hinfo = get_hardware_type_and_id(run_id)

    if acq_types is None:
        if hinfo[0] == 'LCA-11021':
            acq_types = ['flat_pair_raft_acq']
        else:
            acq_types = ['FLAT']

    return get_files_for_run(run_id,
                             imageType="FLAT",
                             testTypes=acq_types,
                             outkey='FLAT',
                             **kwargs)

