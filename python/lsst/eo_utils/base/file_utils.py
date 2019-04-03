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

SLOT_FORMAT_STRING = '{outdir}/{fileType}/{raft}/{testType}/{raft}-{run_num}-{slot}{suffix}'
RAFT_FORMAT_STRING = '{outdir}/{fileType}/{raft}/{testType}/{raft}-{run_num}{suffix}'

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


def get_slot_file_basename(**kwargs):
    """Return the filename for a mask file

    The format is {outdir}/{fileType}/{raft}/{testType}/{raft}-{run_num}-{slot}{suffix}

    @param kwargs:
        outdir (str)
        fileType (str)
        raft (str)
        testType (str)
        run_num (str)
        slot (str)
        suffix (str)

    @returns (str) The path for the file.
    """
    return str(SLOT_FORMAT_STRING.format(**kwargs))


def get_raft_file_basename(**kwargs):
    """Return the filename for a mask file

    The format is {outdir}/{fileType}/{raft}/{testType}/{raft}-{run_num}{suffix}

    @param kwargs:
        outdir (str)
        fileType (str)
        raft (str)
        testType (str)
        run_num (str)
        suffix (str)

    @returns (str) The path for the file.
    """
    return str(RAFT_FORMAT_STRING.format(**kwargs))



def mask_filename(outdir, raft, run_num, slot, **kwargs):
    """Return the filename for a mask file

    The format is {outdir}/masks/{raft}/{raft}-{run_num}-{slot}_mask.fits

    @returns (str) The path for the file.
    """
    return get_slot_file_basename(outdir=outdir, fileType='masks',
                                  raft=raft, testType='', run_num=run_num,
                                  slot=slot, suffix=kwargs.get('suffix', '_mask.fits'))


def get_files_for_run(run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       testTypes (list)  The types of acquistions we want to include
       imageType (str)   The image type we want
       outkey (str)      Where to put the output file
       matchstr (str)    If set, only inlcude files with this string
       nfiles (int)      Number of files to include per test

    @returns (dict) Dictionary mapping slot to file names
    """
    testTypes = kwargs.get('testTypes')
    imageType = kwargs.get('imageType')
    outkey = kwargs.get('outkey', imageType)
    matchstr = kwargs.get('matchstr', None)
    nfiles = kwargs.get('nfiles', None)

    outdict = {}

    if run_id.find('D') >= 0:
        db = 'Dev'
    else:
        db = 'Prod'
    handler = get_EO_analysis_files(db=db)
    hinfo = get_hardware_type_and_id(run_id)

    for test_type in testTypes:
        r_dict = handler.get_files(testName=test_type, run=run_id, imgtype=imageType, matchstr=matchstr)
        for key, val in r_dict.items():
            if hinfo[0] == 'LCA-11021':
                # Raft level data
                if nfiles is None:
                    filelist = val
                else:
                    filelist = val[0:min(nfiles, len(val))]
                if key in outdict:
                    outdict[key][outkey] += filelist
                else:
                    outdict[key] = {outkey:filelist}
            else:
                # BOT level data, need to add extra layer
                if key not in outdict:
                    outdict[key] = {}
                for key2, val2 in val.items():
                    if nfiles is None:
                        filelist = val2
                    else:
                        filelist = val2[0:min(nfiles, len(val2))]
                    if key2 in outdict[key]:
                        outdict[key][key2][outkey] += filelist
                    else:
                        outdict[key][key2] = {outkey:filelist}

    if hinfo[0] == 'LCA-11021':
        return {hinfo[1]:outdict}

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
        mask_files = [mask_filename(**kwargs)]
    else:
        mask_files = []
    return mask_files


def read_runlist(filepath):
    """Read a list of runs from a txt file

    @param filepath (str)    The input file with the list of runs.
                             Each line should contain raft and run number, e.g.,
                             RTM-004-Dev 6106D

    @returns (list)          A list of tuples with (raft, run_num)
    """
    fin = open(filepath)
    lin = fin.readline()

    outlist = []
    while lin:
        tokens = lin.split()
        if len(tokens) == 2:
            outlist.append(tokens)
        lin = fin.readline()
    return outlist
