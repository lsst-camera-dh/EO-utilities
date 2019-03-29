#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

import os

from get_EO_analysis_files import get_EO_analysis_files

#ACQ_TYPES_DEFAULT = ['fe55_raft_acq',
#                     'flat_pair_raft_acq',
#                     'sflat_raft_acq',
#                     'qe_raft_acq',
#                     'dark_raft_acq']
ACQ_TYPES_DEFAULT = ['dark_raft_acq']




def superbias_filename(outdir, raft, run_num, slot, superbias, **kwargs):
    """Return the filename for a superbias file

    The format is {outdir}/{raft}/{raft}-{run_num}-{slot}_superbias_b-{bias_type}.fits

    @param outdir(str)
    @param raft(str)
    @param run_num(str)
    @param slot(str)
    @param superbias(str)
    @param kwargs (dict)
        std (bool)

    @returns (str) The path for the file.
    """
    outpath = os.path.join(outdir, raft,
                           '%s-%s-%s_superbias_b-%s' % (raft, run_num, slot, superbias))

    if kwargs.get('std', False):
        outpath += "_std"

    outpath += '.fits'
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
        std (bool)

    @returns (str) The path for the file.
    """
    stat_type = kwargs['stat_type']
    bias_type = kwargs.get('bias', None)

    outpath = os.path.join(outdir, raft,
                           '%s-%s-%s_%s_b-%s' %\
                               (raft, run_num, slot, stat_type.lower(), bias_type))

    if kwargs.get('std', False):
        outpath += "_std"

    outpath += '.fits'
    return outpath


def raft_basename(outdir, raft, run_num, **kwargs):
    """Return the filename for a raft level plot

    The format is {outdir}/plots/{raft}/{raft}-{run_num}-{slot}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    """
    outbase = os.path.join(outdir, "plots", raft,
                           "%s-%s" % (raft, run_num))
    return outbase



def bias_basename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a bias file

    The format is {outdir}/plots/{raft}/{raft}-{run_num}-{slot}_{plotname}_b-{bias_type}_s-{superbias_type}

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
    bias_type = kwargs.get('bias', None)
    superbias_type = kwargs.get('superbias', None)

    outpath = os.path.join(outdir, "plots", raft,
                           "%s-%s-%s" % (raft, run_num, slot))

    if bias_type is None:
        outpath += "_b-none"
    else:
        outpath += "_b-%s" % bias_type

    if superbias_type is None:
        outpath += "_s-none"
    else:
        outpath += "_s-%s" % superbias_type

    if kwargs.get('std', False):
        outpath += "_std"

    return outpath


def superbias_basename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a plot made from a superbias file

    The format is {outdir}/plots/{raft}/{raft}-{run_num}-{slot}_b-{superbias_type}

    @param outdir (str)
    @param raft (str)
    @param run_num (str)
    @param slot (str)
    @param kwargs (dict)
        superbias_type(str)
        std (bool)

    @returns (str) The path for the file.
    """
    superbias_type = kwargs.get('superbias')
    outpath = os.path.join(outdir, "plots", raft,
                           "%s-%s-%s" % (raft, run_num, slot))

    if superbias_type is None:
        outpath += "_b-none"
    else:
        outpath += "_b-%s" % superbias_type

    if kwargs.get('std', False):
        outpath += "_std"

    return outpath



def get_bias_files_run(run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include
 
    @returns (dict) Dictionary mapping slot to file names
    """
    outdict = {}
    if kwargs.get('acq_types', None) is None:
        acq_types = ACQ_TYPES_DEFAULT

    if run_id.find('D') >= 0:
        db = 'Dev'
    else:
        db = 'Prod'
    handler = get_EO_analysis_files(db=db)

    for acq_type in acq_types:
        r_dict = handler.get_files(testName=acq_type, run=run_id, imgtype='BIAS')
        for key, val in r_dict.items():
            if key in outdict:
                outdict[key]["BIAS"] += val
            else:
                outdict[key] = dict(BIAS=val)

    return outdict

