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
    hid = tokens[1].replace('-Dev', '')
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

    suffix = kwargs.get('suffix', None)
    if suffix is not None:
        outpath += '_suffix'

    outpath += '.fits'
    return outpath


def get_files_for_run(run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       testTypes (list)  The types of acquistions we want to include
       imageType (str)   The image type we want
       outkey (str)      Where to put the output file
       matchstr (str)    If set, only inlcude files with this string

    @returns (dict) Dictionary mapping slot to file names
    """
    testTypes = kwargs.get('testTypes')
    imageType = kwargs.get('imageType')
    outkey = kwargs.get('outkey')
    matchstr = kwargs.get('matchstr', None)

    outdict = {}

    if run_id.find('D') >= 0:
        db = 'Dev'
    else:
        db = 'Prod'
    handler = get_EO_analysis_files(db=db)

    for test_type in testTypes:
        r_dict = handler.get_files(testName=test_type, run=run_id, imgtype=imageType)
        for key, val in r_dict.items():
            matchfiles = []
            if matchstr is not None:
                for fname in val:
                    if fname.find(matchstr) < 0:
                        continue
                    matchfiles.append(fname)
            if key in outdict:
                outdict[key][outkey] += matchfiles
            else:
                outdict[key] = {outkey:matchfiles}

    return outdict


def get_mask_files_run(run_id, **kwargs):
    """Get a set of mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       mask_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    mask_types = kwargs.get('mask_types', None)
    if mask_types is None:
        mask_types = MASK_TYPES_DEFAULT

    return get_files_for_run(run_id,
                             testTypes=mask_types,
                             outkey='MASK',
                             matchstr='_mask')


def get_mask_files(**kwargs):
    """Get a set of mask files based on the kwargs

    @param kwargs
       mask (bool)  Flag to actually get the mask files

    @return (list) List of files
    """
    if kwargs.get('mask', False):
        mask_files = [mask_filename('masks', **kwargs)]
    else:
        mask_files = None
    return mask_files
