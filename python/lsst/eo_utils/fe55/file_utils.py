#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import DATACAT_TS8_TEST_TYPES, DATACAT_BOT_TEST_TYPES

from lsst.eo_utils.base.config_utils import copy_dict

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    get_slot_file_basename, get_raft_file_basename, get_summary_file_basename

from lsst.eo_utils.bias.file_utils import get_bias_suffix


RAFT_FE55_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='fe55', run=None, suffix='')
RAFT_FE55_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='fe55', run=None, suffix='')
SLOT_FE55_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='fe55', run=None, slot=None, suffix='')
SLOT_FE55_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='fe55', run=None, slot=None, suffix='')


FE55_SUMMARY_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables',
                                       testType='fe55', dataset=None, suffix='')
FE55_SUMMARY_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots',
                                      testType='fe55', dataset=None, suffix='')


def raft_fe55_tablename(caller, **kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/tables/{raft}/fe55/{raft}-{run}-RFT{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs:          Passed to get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_FE55_TABLENAME_DEFAULTS)
    if kwargs.get('use_all', False):
        kwcopy['suffix'] = '_all%s' % kwcopy['suffix']
    else:
        kwcopy['suffix'] = '_good%s' % kwcopy['suffix']
    return get_raft_file_basename(caller, **kwcopy)


def raft_fe55_plotname(caller, **kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/plots/{raft}/fe55/{raft}-{run}-{slot}{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs:          Passed to get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_FE55_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)
    if kwargs.get('use_all', False):
        kwcopy['suffix'] = '_all%s' % kwcopy['suffix']
    else:
        kwcopy['suffix'] = '_good%s' % kwcopy['suffix']
    return get_raft_file_basename(caller, **kwcopy)


def slot_fe55_tablename(caller, **kwargs):
    """Return the filename for a plot made from a fe55 file

    The format is {outdir}/tables/{raft}/fe55/{raft}-{run}-{slot}{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs           Passed to get_fe55_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_FE55_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)
    return get_slot_file_basename(caller, **kwcopy)


def slot_fe55_plotname(caller, **kwargs):
    """Return the filename for a plot made from a fe55 file

    The format is {outdir}/plots/{raft}/fe55/{raft}-{run}-{slot}{suffix}

    @param kwargs           Passed to get_fe55_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_FE55_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)
    return get_slot_file_basename(caller, **kwcopy)


def fe55_summary_tablename(caller, **kwargs):
    """Return the filename for a summary table file

    The format is {outdir}/tables/summary/fe55/{dataset}{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, FE55_SUMMARY_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)
    if kwargs.get('use_all', False):
        kwcopy['suffix'] = '_all%s' % kwcopy['suffix']
    else:
        kwcopy['suffix'] = '_good%s' % kwcopy['suffix']
    return get_summary_file_basename(caller, **kwcopy)


def fe55_summary_plotname(caller, **kwargs):
    """Return the filename for a summary plot file

    The format is {outdir}/plots/summary/fe55/{dataset}{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, FE55_SUMMARY_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)
    if kwargs.get('use_all', False):
        kwcopy['suffix'] = '_all%s' % kwcopy['suffix']
    else:
        kwcopy['suffix'] = '_good%s' % kwcopy['suffix']
    return get_summary_file_basename(caller, **kwcopy)

def get_fe55_files_run(run_id, **kwargs):
    """Get a set of fe55 and mask files out of a folder

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
                             imageType="FE55",
                             testTypes=acq_types,
                             outkey='FE55',
                             **kwargs)
