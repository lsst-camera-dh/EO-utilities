#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import DATACAT_TS8_TEST_TYPES, DATACAT_BOT_TEST_TYPES

from lsst.eo_utils.base.config_utils import copy_dict

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    get_slot_file_basename, get_raft_file_basename, get_summary_file_basename



RAFT_FLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='flat', run_num=None)
RAFT_FLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='flat', run_num=None)
SLOT_FLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='flat', run_num=None, slot=None)
SLOT_FLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='flat', run_num=None, slot=None)

RAFT_SFLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                     testType='superflat', run_num=None)
RAFT_SFLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                    testType='superflat', run_num=None)
SLOT_SFLAT_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                     testType='superflat', run_num=None, slot=None)
SLOT_SFLAT_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                    testType='superflat', run_num=None, slot=None)

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
    kwcopy['suffix'] = get_flat_suffix(**kwargs)

    outbase = get_raft_file_basename(**kwcopy)

    return str(outbase)

def raft_flat_plotname(**kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/plots/{raft}/flat/{raft}-{run_num}-{slot}_b-{flat_type}_s-{superflat_type}{suffix}

    @param kwargs:          Passed to get_flat_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_FLAT_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_flat_suffix(**kwargs)

    outbase = get_raft_file_basename(**kwcopy)
    return str(outbase)


def get_flat_suffix(**kwargs):
    """Return the suffix for flat files

    @param kwargs (dict)
        flat_type(str)
        superflat_type(str)
        stat (str)
        std (bool)
        suffix (str)

    the format is _b-{flat_type}_s-{superflat_type}{stat}{suffix}
    @return (str) the suffix
    """
    flat_type = kwargs.get('flat', None)
    superflat_type = kwargs.get('superflat', None)
    kwsuffix = kwargs.get('suffix', None)
    stat_type = kwargs.get('stat', None)

    suffix = ""
    if flat_type is None:
        suffix += "_b-none"
    else:
        suffix += "_b-%s" % flat_type

    if superflat_type is None:
        suffix += "_s-none"
    else:
        suffix += "_s-%s" % superflat_type

    if kwargs.get('std', False):
        suffix += "_std"

    if stat_type is not None:
        suffix += "_%s" % stat_type

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix


def get_superflat_suffix(**kwargs):
    """Return the suffix for flat files

    @param kwargs (dict)
        superflat_type(str)
        std (bool)
        suffix (str)
        stat (str)

    the format is b-{superflat_type}{stat}{suffix}
    @return (str) the suffix
    """
    superflat_type = kwargs.get('superflat', None)
    stat_type = kwargs.get('stat', None)
    kwsuffix = kwargs.get('suffix', None)
    suffix = ""

    if superflat_type is None:
        suffix += "_b-none"
    else:
        suffix += "_b-%s" % (superflat_type)

    if kwargs.get('std', False):
        suffix += "_std"

    if stat_type is not None:
        suffix += "_%s" % stat_type

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix



def slot_flat_tablename(**kwargs):
    """Return the filename for a plot made from a flat file

    The format is {outdir}/tables/{raft}/flat/{raft}-{run_num}-{slot}_b-{flat_type}_s-{superflat_type}

    @param kwargs           Passed to get_flat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_FLAT_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_flat_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_flat_plotname(**kwargs):
    """Return the filename for a plot made from a flat file

    The format is {outdir}/plots/{raft}/flat/{raft}-{run_num}-{slot}_b-{flat_type}_s-{superflat_type}

    @param kwargs           Passed to get_flat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_FLAT_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_flat_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_superflat_tablename(**kwargs):
    """Return the filename for a plot made from a superflat file

    The format is {outdir}/tables/{raft}/superflat/{raft}-{run_num}-{slot}_b-{superflat_type}

    @param kwargs           Passed to get_superflat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_SFLAT_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_superflat_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_superflat_plotname(**kwargs):
    """Return the filename for a plot made from a superflat file

    @param kwargs           Passed to get_superflat_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_SFLAT_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_superflat_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def raft_superflat_tablename(**kwargs):
    """Return the filename for a plot made from a superflat file

    The format is {outdir}/tables/{raft}/superflat/{raft}-{run_num}-{slot}_b-{superflat_type}

    @param kwargs           Passed to get_superflat_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_SFLAT_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_superflat_suffix(**kwargs)
    outpath = get_raft_file_basename(**kwcopy)

    return str(outpath)

def raft_superflat_plotname(**kwargs):
    """Return the filename for a plot made from a superflat file

    The format is {outdir}/plots/{raft}/superflat/{raft}-{run_num}-{slot}_b-{superflat_type}

    @param kwargs           Passed to get_superflat_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_SFLAT_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_superflat_suffix(**kwargs)
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
            acq_types = DATACAT_TS8_TEST_TYPES
        else:
            acq_types = DATACAT_BOT_TEST_TYPES

    return get_files_for_run(run_id,
                             imageType="FLAT",
                             testTypes=acq_types,
                             outkey='FLAT',
                             **kwargs)

