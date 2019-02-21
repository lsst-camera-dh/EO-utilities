#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

import os

from get_EO_analysis_files import get_EO_analysis_files
from exploreRun import exploreRun

ACQ_TYPES_DEFAULT = ['fe55_raft_acq',
                     'flat_pair_raft_acq',
                     'sflat_raft_acq',
                     'qe_raft_acq',
                     'dark_raft_acq']

MASK_TYPES_DEFAULT = ['fe55_raft_analysis',
                      'dark_defects_raft',
                      'traps_raft',
                      'bright_defects_raft']

RD_ROOT_FOLDER = '/gpfs/slac/lsst/fs1/g/data/R_and_D/'
RAFT_ROOT_FOLDER = '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM/'
DEFAULT_DB = 'Dev'


def makedir_safe(filepath):
    """Make a directory needed to write a file

    @param filepath (str)    The file we are going to write
    """
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass


def get_hardware_type_and_id(db, run_num):
    """Return the hardware type and hardware id for a given run

    @param db(str)        The database we are reading from, either 'Dev' or 'Prod'
    @param run_num(str)   The number number we are reading

    @returns (tuple)
      htype (str) The hardware type, eitherL
                        'LCA-10134' (aka full crystat) or
                        'LCA-11021' (single raft)
      hid (str) The hardware id, e.g., RMT-004-Dev
    """
    er = exploreRun(db=db)
    hsn = er.hardware_sn(run=run_num)
    tokens = hsn.split('_')
    htype = tokens[0]
    hid = tokens[1]
    return (htype, hid)


def superbias_filename(outdir, raft, run_num, slot, bias_type):
    """Return the filename for a superbias file

    The format is {outdir}/{raft}/{raft}-{run_num}-{slot}_superbias_b-{bias_type}.fits

    @param outdir(str)
    @param raft(str)
    @param run_num(str)
    @param slot(str)
    @param bias_type(str)

    @returns (str) The path for the file.
    """
    outpath = os.path.join(outdir, raft,
                           '%s-%s-%s_superbias_b-%s.fits' % (raft, run_num, slot, bias_type))
    return outpath


def superbias_stat_filename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a superbias-like statistics file

    The format is {outdir}/{raft}/{raft}-{run_num}-{slot}_{stat_type}_b-{superbias_type}.fits

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        stat_type(str)
        bias_type(str)

    @returns (str) The path for the file.
    """
    stat_type = kwargs['stat_type']
    bias_type = kwargs.get('bias_type', None)

    outpath = os.path.join(outdir, raft,
                           '%s-%s-%s_%s_b-%s.fits' %\
                               (raft, run_num, slot, stat_type.lower(), bias_type))
    return outpath


def bias_plot_basename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a bias file

    The format is {outdir}/plots/{raft}/{raft}-{run_num}-{slot}_{plotname}_b-{bias_type}_s-{superbias_type}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        plotname (str)
        bias_type(str)
        superbias_type(str)

    @returns (str) The path for the file.
    """
    bias_type = kwargs.get('bias_type', None)
    superbias_type = kwargs.get('superbias_type', None)

    outpath = os.path.join(outdir, "plots", raft,
                           "%s-%s-%s_%s" % (raft, run_num, slot, kwargs['plotname']))

    if bias_type is None:
        outpath += "_b-none"
    else:
        outpath += "_b-%s" % bias_type

    if superbias_type is None:
        outpath += "_s-none"
    else:
        outpath += "_s-%s" % superbias_type

    return outpath


def superbias_plot_basename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a superbias file

    The format is {outdir}/plots/{raft}/{raft}-{run_num}-{slot}_{plotname}_b-{superbias_type}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        plotname(str)
        superbias_type(str)

    @returns (str) The path for the file.
    """
    superbias_type = kwargs.get('superbias_type')
    outpath = os.path.join(outdir, "plots", raft,
                           "%s-%s-%s_%s" % (raft, run_num, slot, kwargs['plotname']))

    if superbias_type is None:
        outpath += "_b-none"
    else:
        outpath += "_b-%s" % superbias_type

    return outpath


def get_bias_files_run(run_id, acq_types=None, db=DEFAULT_DB):
    """Get a set of bias files out of a folder

    @param run_id (str)     The number number we are reading
    @param acq_types (list) The types of acquistions we want to include
    @param db (str)         The database we are reading from, either 'Dev' or 'Prod'

    @returns (dict) Dictionary mapping slot to file names
    """
    outdict = {}
    if acq_types is None:
        acq_types = ACQ_TYPES_DEFAULT

    handler = get_EO_analysis_files(db=db)
    for acq_type in acq_types:
        r_dict = handler.get_files(testName=acq_type, run=run_id, imgtype='BIAS')
        for key, val in r_dict.items():
            if key in outdict:
                outdict[key] += val
            else:
                outdict[key] = val
    return outdict


def get_mask_files_run(run_id, mask_types=None, db=DEFAULT_DB):
    """Get a set of bias files out of a folder

    @param run_id (str)      The number number we are reading
    @param mask_types (list) The types of masks we want to include
    @param db (str)          The database we are reading from, either 'Dev' or 'Prod'

    @returns (dict) Dictionary mapping slot to file names
    """
    outdict = {}
    if mask_types is None:
        mask_types = MASK_TYPES_DEFAULT


    handler = get_EO_analysis_files(db=db)
    for mask_type in mask_types:
        r_dict = handler.get_files(testName=mask_type, run=run_id, imgtype='FLAT')
        for key, val in r_dict.items():
            if key in outdict:
                outdict[key] += val
            else:
                outdict[key] = val
    return outdict



def get_bias_and_mask_files_run(run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include
       mask_types (list) The types of masks we want to include
       db (str)          The database we are reading from, either 'Dev' or 'Prod'
       mask (bool)       Flag to include mask files

    @returns (dict) Dictionary mapping slot to file names
    """
    outdict = {}
    if kwargs.get('acq_types', None) is None:
        acq_types = ACQ_TYPES_DEFAULT
    if kwargs.get('mask', False):
        if kwargs.get('mask_types', None) is None:
            mask_types = MASK_TYPES_DEFAULT
    else:
        mask_types = []

    handler = get_EO_analysis_files(db=kwargs.get('db', DEFAULT_DB))
    for acq_type in acq_types:
        r_dict = handler.get_files(testName=acq_type, run=run_id, imgtype='BIAS')
        for key, val in r_dict.items():
            if key in outdict:
                outdict[key]["bias_files"] += val
            else:
                outdict[key] = dict(bias_files=val, mask_files=[])

        for mask_type in mask_types:
            r_dict = handler.get_files(testName=mask_type, run=run_id, imgtype='FLAT')
            for key, val in r_dict.items():
                if key in outdict:
                    outdict[key]["mask_files"] += val
                else:
                    outdict[key] = dict(bias_files=[], mask_files=val)

    return outdict
