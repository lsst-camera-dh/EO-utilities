#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

import os

from get_EO_analysis_files import get_EO_analysis_files
from exploreRun import exploreRun

MASK_TYPES_DEFAULT = ['fe55_raft_analysis',
                      'dark_defects_raft',
                      'traps_raft',
                      'bright_defects_raft']

#MASK_TYPES_DEFAULT = []


def makedir_safe(filepath):
    """Make a directory needed to write a file

    @param filepath (str)    The file we are going to write
    """
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass


def get_hardware_type_and_id(run_num):
    """return the hardware type and hardware id for a given run

    @param run_num(str)   The number number we are reading

    @returns (tuple)
      htype (str) The hardware type, either
                        'LCA-10134' (aka full camera) or
                        'LCA-11021' (single raft)
      hid (str) The hardware id, e.g., RMT-004-Dev
    """
    if run_num.find('D') >= 0:
        db = 'Dev'
    else:
        db = 'Prod'
    er = exploreRun(db=db)
    hsn = er.hardware_sn(run=run_num)
    tokens = hsn.split('_')
    htype = tokens[0]
    hid = tokens[1]
    return (htype, hid)


def mask_filename(maskdir, raft, run_num, slot, **kwargs):
    """Return the filename for a mask file

    The format is {maskdir}/{raft}/{raft}-{run_num}-{slot}_mask.fits

    @param maskdir(str)
    @param raft(str)
    @param run_num(str)
    @param slot(str)

    @returns (str) The path for the file.
    """
    outpath = os.path.join(maskdir, raft,
                           '%s-%s-%s_mask' % (raft, run_num, slot))

    outpath += '.fits'
    return outpath

