#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type using the data Butler"""

from lsst.daf.persistence import Butler

from lsst.eo_utils.base.butler_utils import getDataRefList

BIAS_TEST_TYPES = ["DARK", "FLAT", "FE55", "PPUMP", "SFLAT", "SFLAT", "LAMBDA", "TRAP"]


def get_bias_files_butler(butler, run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param butler (Butler)    The bulter we are using
    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include
       mask (bool)       Flag to include mask files

    @returns (dict) Dictionary mapping slot to file names
    """
    outdict = {}
    if kwargs.get('acq_types', None) is None:
        acq_types = BIAS_TEST_TYPES

    bias_kwargs = dict(imageType='BIAS', testType=acq_types)

    slots = butler.queryMetadata('raw', 'detectorName', dict(run=run_id))

    for slot in slots:
        bias_kwargs['detectorName'] = slot
        outdict[slot] = dict(BIAS=getDataRefList(butler, run_id, **bias_kwargs))
    return outdict

