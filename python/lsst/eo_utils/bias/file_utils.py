#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import DATACAT_TS8_TEST_TYPES, DATACAT_BOT_TEST_TYPES,\
     DEFAULT_SUPERBIAS_TYPE

from lsst.eo_utils.base.config_utils import copy_dict

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    get_slot_file_basename, get_raft_file_basename, get_summary_file_basename
from lsst.eo_utils.base.image_utils import get_ccd_from_id


def superbias_filename(outdir, raft, run, slot, **kwargs):
    """Return the filename for a superbias file

    The format is {outdir}/superbias/{raft}/{raft}-{run}-{slot}_superbias_b-{bias_type}.fits

    @param outdir (str)
    @param raft (str)
    @param run (str)
    @param slot (str)
    @param bias_type (str)
    @param kwargs:
        bias_type (str)
        suffix (str)

    @returns (str) The path for the file.
    """
    suffix = '_superbias_b-{bias_type}'.format(**kwargs)

    outpath = get_slot_file_basename(outdir=outdir, fileType='superbias',
                                     raft=raft, testType='', run=run,
                                     slot=slot, suffix=suffix)
    outpath += '.fits'
    return str(outpath)


def superbias_stat_filename(outdir, raft, run, slot, **kwargs):
    """Return the filename for a superbias-like statistics file

    The format is {outdir}/superbias/{raft}/{raft}-{run}-{slot}_{stat_type}_b-{superbias_type}.fits

    @param outdir (str)
    @param raft (str)
    @param run (str)
    @param slot (str)
    @param kwargs (dict)
        stat_type(str)
        bias_type(str)

    @returns (str) The path for the file.
    """
    suffix = '_{stat_type}_b-{bias_type}'.format(**kwargs)

    outpath = get_slot_file_basename(outdir=outdir, fileType='superbias',
                                     raft=raft, testType='', run=run,
                                     slot=slot, suffix=suffix)
    outpath += '.fits'
    return str(outpath)


RAFT_BIAS_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='bias', run=None)
RAFT_BIAS_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='bias', run=None)
SLOT_BIAS_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                    testType='bias', run=None, slot=None)
SLOT_BIAS_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                   testType='bias', run=None, slot=None)

RAFT_SBIAS_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                     testType='superbias', run=None)
RAFT_SBIAS_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                    testType='superbias', run=None)
SLOT_SBIAS_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables', raft=None,
                                     testType='superbias', run=None, slot=None)
SLOT_SBIAS_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots', raft=None,
                                    testType='superbias', run=None, slot=None)

BIAS_SUMMARY_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables',
                                       testType='bias', dataset=None, suffix='')
BIAS_SUMMARY_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots',
                                      testType='bias', dataset=None, suffix='')
SBIAS_SUMMARY_TABLENAME_DEFAULTS = dict(outdir='analysis', fileType='tables',
                                        testType='superbias', dataset=None, suffix='')
SBIAS_SUMMARY_PLOTNAME_DEFAULTS = dict(outdir='analysis', fileType='plots',
                                       testType='superbias', dataset=None, suffix='')


def raft_bias_tablename(caller, **kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/tables/{raft}/bias/{raft}-{run}-RFT_b-{bias_type}_s-{superbias_type}{suffix}

    @param kwargs:          Passed to get_bias_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_BIAS_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)

    outbase = get_raft_file_basename(**kwcopy)

    return str(outbase)

def raft_bias_plotname(caller, **kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/plots/{raft}/bias/{raft}-{run}-{slot}_b-{bias_type}_s-{superbias_type}{suffix}

    @param kwargs:          Passed to get_bias_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_BIAS_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)

    outbase = get_raft_file_basename(**kwcopy)
    return str(outbase)


def get_bias_suffix(**kwargs):
    """Return the suffix for bias files

    @param kwargs (dict)
        bias_type(str)
        superbias_type(str)
        stat (str)
        std (bool)
        suffix (str)

    the format is _b-{bias_type}_s-{superbias_type}{stat}{suffix}
    @return (str) the suffix
    """
    bias_type = kwargs.get('bias', None)
    superbias_type = kwargs.get('superbias', None)
    kwsuffix = kwargs.get('suffix', None)
    stat_type = kwargs.get('stat', None)

    suffix = ""
    if bias_type is None:
        suffix += "_b-none"
    else:
        suffix += "_b-%s" % bias_type

    if superbias_type is None:
        suffix += "_s-none"
    else:
        suffix += "_s-%s" % superbias_type

    if kwargs.get('std', False):
        suffix += "_std"

    if stat_type is not None:
        suffix += "_%s" % stat_type

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix


def get_superbias_suffix(**kwargs):
    """Return the suffix for bias files

    @param kwargs (dict)
        superbias_type(str)
        std (bool)
        suffix (str)
        stat (str)

    the format is b-{superbias_type}{stat}{suffix}
    @return (str) the suffix
    """
    superbias_type = kwargs.get('superbias', None)
    stat_type = kwargs.get('stat', None)
    kwsuffix = kwargs.get('suffix', None)
    suffix = ""

    if superbias_type is None:
        suffix += "_b-none"
    else:
        suffix += "_b-%s" % (superbias_type)

    if kwargs.get('std', False):
        suffix += "_std"

    if stat_type is not None:
        suffix += "_%s" % stat_type

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix



def slot_bias_tablename(caller, **kwargs):
    """Return the filename for a plot made from a bias file

    The format is {outdir}/tables/{raft}/bias/{raft}-{run}-{slot}_b-{bias_type}_s-{superbias_type}

    @param kwargs           Passed to get_bias_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_BIAS_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_bias_plotname(caller, **kwargs):
    """Return the filename for a plot made from a bias file

    The format is {outdir}/tables/{raft}/bias/{raft}-{run}-{slot}_b-{bias_type}_s-{superbias_type}

    @param kwargs           Passed to get_bias_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_BIAS_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_bias_plotname(caller, **kwargs):
    """Return the filename for a plot made from a bias file

    The format is {outdir}/plots/{raft}/bias/{raft}-{run}-{slot}_b-{bias_type}_s-{superbias_type}

    @param kwargs           Passed to get_bias_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_BIAS_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_bias_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_superbias_tablename(caller, **kwargs):
    """Return the filename for a plot made from a superbias file

    The format is {outdir}/tables/{raft}/superbias/{raft}-{run}-{slot}_b-{superbias_type}

    @param kwargs           Passed to get_superbias_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_SBIAS_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_superbias_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def slot_superbias_plotname(caller, **kwargs):
    """Return the filename for a plot made from a superbias file

    @param kwargs           Passed to get_superbias_suffix and get_slot_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SLOT_SBIAS_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_superbias_suffix(**kwargs)

    outpath = get_slot_file_basename(**kwcopy)
    return str(outpath)


def raft_superbias_tablename(caller, **kwargs):
    """Return the filename for a plot made from a superbias file

    The format is {outdir}/tables/{raft}/superbias/{raft}-{run}-{slot}_b-{superbias_type}

    @param kwargs           Passed to get_superbias_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_SBIAS_TABLENAME_DEFAULTS)
    kwcopy['suffix'] = get_superbias_suffix(**kwargs)
    outpath = get_raft_file_basename(**kwcopy)

    return str(outpath)

def raft_superbias_plotname(caller, **kwargs):
    """Return the filename for a plot made from a superbias file

    The format is {outdir}/plots/{raft}/superbias/{raft}-{run}-{slot}_b-{superbias_type}

    @param kwargs           Passed to get_superbias_suffix and get_raft_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, RAFT_SBIAS_PLOTNAME_DEFAULTS)
    kwcopy['suffix'] = get_superbias_suffix(**kwargs)
    outpath = get_raft_file_basename(**kwcopy)

    return str(outpath)


def bias_summary_tablename(caller, **kwargs):
    """Return the filename for a summary table file

    The format is {outdir}/tables/summary/bias/{dataset}{suffix}

    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, BIAS_SUMMARY_TABLENAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)
    return str(outpath)

def bias_summary_plotname(caller, **kwargs):
    """Return the filename for a summary plot file

    The format is {outdir}/plots/summary/bias/{dataset}{suffix}

    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, BIAS_SUMMARY_PLOTNAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)
    return str(outpath)

def superbias_summary_tablename(caller, **kwargs):
    """Return the filename for a summary table file

    The format is {outdir}/tables/summary/bias/{dataset}{suffix}

    @param kwargs           Passed to get_summary_file_basename

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SBIAS_SUMMARY_TABLENAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)
    return str(outpath)


def superbias_summary_plotname(caller, **kwargs):
    """Return the filename for a summary plot file

    The format is {outdir}/plots/summary/bias/{dataset}{suffix}

    @returns (str) The path for the file.
    """
    kwcopy = copy_dict(kwargs, SBIAS_SUMMARY_PLOTNAME_DEFAULTS)
    outpath = get_summary_file_basename(**kwcopy)

    return str(outpath)

def get_bias_files_run(run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

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
                             imageType="BIAS",
                             testTypes=acq_types,
                             outkey='BIAS',
                             **kwargs)


def get_superbias_frame(**kwargs):
    """Get the superbias frame

    @param kwargs
       superbias_type (str)
       run_id (str)           The number number we are reading

    @returns (dict) Dictionary mapping slot to file names
    """
    kwcopy = kwargs.copy()
    superbias_type = kwcopy.pop('superbias', DEFAULT_SUPERBIAS_TYPE)
    stat_type = kwcopy.pop('stat', None)
    mask_files = kwcopy.pop('mask_files', [])

    if stat_type is None:
        if superbias_type is None:
            return None
        superbias_file = superbias_filename(bias_type=superbias_type, **kwcopy)
    else:
        superbias_file = superbias_stat_filename(bias_type=superbias_type, stat_type=stat_type, **kwargs)
    return get_ccd_from_id(None, superbias_file, mask_files)
