#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    get_slot_file_basename, get_raft_file_basename
from lsst.eo_utils.base.image_utils import get_ccd_from_id

ACQ_TYPES_RAFT = ['fe55_raft_acq',
                  'flat_pair_raft_acq',
                  'sflat_raft_acq',
                  'qe_raft_acq',
                  'dark_raft_acq']

ACQ_TYPES_BOT = ['DARK', 'FLAT', 'FE55', 'PPUMP', 'SFLAT', 'LAMBDA', 'TRAP']

DEFAULT_SUPERBIAS_TYPE = None



def superbias_filename(outdir, raft, run_num, slot, superbias, **kwargs):
    """Return the filename for a superbias file

    The format is {outdir}/superbias/{raft}/{raft}-{run_num}-{slot}_superbias_b-{bias_type}.fits

    @param outdir(str)
    @param raft(str)
    @param run_num(str)
    @param slot(str)
    @param superbias(str)
    @param kwargs (dict)
        std (bool)

    @returns (str) The path for the file.
    """
    suffix = '_superbias_b-%s' % superbias
    if kwargs.get('std', False):
        suffix += "_std"

    outpath = get_slot_file_basename(outdir=outdir, fileType='superbias',
                                     raft=raft, testType='', run_num=run_num,
                                     slot=slot, suffix=suffix)
    outpath += '.fits'
    return str(outpath)


def superbias_stat_filename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a superbias-like statistics file

    The format is {outdir}/superbias/{raft}/{raft}-{run_num}-{slot}_{stat_type}_b-{superbias_type}.fits

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        stat_type(str)
        bias_type(str)
        std (bool)

    @returns (str) The path for the file.
    """
    suffix = '_{stat_type}_b-{bias_type}'.format(**kwargs)
    if kwargs.get('std', False):
        suffix += "_std"

    outpath = get_slot_file_basename(outdir=outdir, fileType='superbias',
                                     raft=raft, testType='', run_num=run_num,
                                     slot=slot, suffix=suffix)
    outpath += '.fits'
    return str(outpath)


def raft_bias_tablename(outdir, raft, run_num, **kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/tables/{raft}/bias/{raft}-{run_num}-{slot}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param kwargs
       suffix (str)
    """
    outbase = get_raft_file_basename(outdir=outdir, fileType='tables',
                                     raft=raft, testType='bias', run_num=run_num,
                                     **kwargs)

    return str(outbase)


def raft_bias_plotname(outdir, raft, run_num, **kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/plots/{raft}/bias/{raft}-{run_num}-{slot}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    """
    outbase = get_raft_file_basename(outdir=outdir, fileType='plots',
                                     raft=raft, testType='bias', run_num=run_num,
                                     **kwargs)
    return str(outbase)


def get_bias_suffix(**kwargs):
    """Return the suffix for bias files

    @param kwargs (dict)
        bias_type(str)
        superbias_type(str)
        std (bool)
        suffix (str)

    the format is b-{bias_type}_s-{superbias_type}{suffix}
    @return (str) the suffix
    """
    bias_type = kwargs.get('bias', None)
    superbias_type = kwargs.get('superbias', None)
    kwsuffix = kwargs.get('suffix', None)

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

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix


def get_superbias_suffix(**kwargs):
    """Return the suffix for bias files

    @param kwargs (dict)
        superbias_type(str)
        std (bool)
        suffix (str)

    the format is b-{superbias_type}{suffix}
    @return (str) the suffix
    """
    superbias_type = kwargs.get('superbias', None)
    kwsuffix = kwargs.get('suffix', None)
    suffix = ""

    if superbias_type is None:
        suffix += "_b-none"
    else:
        suffix += "_b-%s" % superbias_type

    if kwargs.get('std', False):
        suffix += "_std"

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix



def slot_bias_tablename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a bias file

    The format is {outdir}/tables/{raft}/bias/{raft}-{run_num}-{slot}_b-{bias_type}_s-{superbias_type}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        bias_type(str)
        superbias_type(str)
        std (bool)

    @returns (str) The path for the file.
    """
    suffix = get_bias_suffix(**kwargs)
    outpath = get_slot_file_basename(outdir=outdir, fileType='tables',
                                     raft=raft, testType='bias', run_num=run_num,
                                     slot=slot, suffix=suffix)
    return str(outpath)


def slot_bias_plotname(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a bias file

    The format is {outdir}/plots/{raft}/bias/{raft}-{run_num}-{slot}_b-{bias_type}_s-{superbias_type}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        bias_type(str)
        superbias_type(str)
        std (bool)

    @returns (str) The path for the file.
    """
    suffix = get_bias_suffix(**kwargs)
    outpath = get_slot_file_basename(outdir=outdir, fileType='plots',
                                     raft=raft, testType='bias', run_num=run_num,
                                     slot=slot, suffix=suffix)
    return str(outpath)


def superbias_tablename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a superbias file

    The format is {outdir}/tables/{raft}/superbias/{raft}-{run_num}-{slot}_b-{superbias_type}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        superbias_type(str)
        std (bool)

    @returns (str) The path for the file.
    """
    suffix = get_superbias_suffix(**kwargs)
    outpath = get_slot_file_basename(outdir=outdir, fileType='tables',
                                     raft=raft, testType='superbias', run_num=run_num,
                                     slot=slot, suffix=suffix)

    return str(outpath)

def superbias_plotname(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a superbias file

    The format is {outdir}/plots/{raft}/superbias/{raft}-{run_num}-{slot}_b-{superbias_type}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        superbias_type(str)
        std (bool)

    @returns (str) The path for the file.
    """
    suffix = get_superbias_suffix(**kwargs)
    outpath = get_slot_file_basename(outdir=outdir, fileType='plots',
                                     raft=raft, testType='superbias', run_num=run_num,
                                     slot=slot, suffix=suffix)

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
            acq_types = ACQ_TYPES_RAFT
        else:
            acq_types = ACQ_TYPES_BOT

    return get_files_for_run(run_id,
                             imageType="BIAS",
                             testTypes=acq_types,
                             outkey='BIAS',
                             **kwargs)


def get_superbias_frame(**kwargs):
    """Get the superbias frame

    @param kwargs
       acq_types (list)  The types of acquistions we want to include

   @param run_id (str)      The number number we are reading

    @returns (dict) Dictionary mapping slot to file names
    """
    superbias_type = kwargs.get('superbias', DEFAULT_SUPERBIAS_TYPE)
    mask_files = kwargs['mask_files']

    if superbias_type is None:
        return None

    superbias_file = superbias_filename(**kwargs)
    return get_ccd_from_id(None, superbias_file, mask_files)
