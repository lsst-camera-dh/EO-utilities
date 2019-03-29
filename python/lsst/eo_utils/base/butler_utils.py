#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type using the data Butler"""

from lsst.daf.persistence import Butler


BUTLER_TS8_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/ts8'
BUTLER_BOT_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/bot'

BUTLER_REPO_DICT = dict(TS8=BUTLER_TS8_REPO,
                        BOT=BUTLER_BOT_REPO)

SLOT_LIST = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']


def getButler(repo, **kwargs):
    """Construct and return a Bulter for the requested repository

    @param: repo (str)     Name of the repo, 'TS8' | 'BOT'
    @param: kwargs (dict)  Passed to the Bulter constructor

    @returns (Bulter) the requested Bulter
    """
    try:
        repo_path = BUTLER_REPO_DICT[repo]
    except KeyError:
        raise KeyError("Unknown Bulter repo key %s" % repo)
    butler = Butler(repo_path, **kwargs)
    return butler


def get_hardware_info(butler, run_num):
    """return the hardware type and hardware id for a given run

    @param: butler (Bulter)  The data Butler
    @param run_num(str)   The number number we are reading

    @returns (tuple)
      htype (str) The hardware type, either
                        'LCA-10134' (aka full camera) or
                        'LCA-11021' (single raft)
      hid (str) The hardware id, e.g., RMT-004
    """
    rafts = butler.queryMetadata('raw', 'raftName', dict(run=run_num))
    if len(rafts) > 1:
        htype = 'LCA-10134'
        hid = 'LCA-10134-0001'
    else:
        htype = 'LCA-11021'
        hid = rafts[0]
    return (htype, hid)


def getVisitList(butler, run_id, **kwargs):
    """Construct and return a list of visit IDs.

    @param: bulter (Bulter)  The data Butler
    @param: run_id (str)     The run ID
    @param: kwargs (dict):
        imageType (str)         The type of image
        testType (str or list)  The type of tests to collect visits from

    @returns (list) a list of the visit IDs
    """

    testType = kwargs.get('testType', None)
    if isinstance(testType, str):
        testTypes = [testType]
    elif isinstance(testType, list):
        testTypes = testType
    elif testType is None:
        testTypes = []
    else:
        raise TypeError("testType must be a list or str or None")

    dataId = dict(run=run_id, imageType=kwargs.get('imageType', 'BIAS'))
    visitList = []
    for testType in testTypes:
        dataId['testType'] = testType
        visitList += butler.queryMetadata("raw", 'visit', dataId)
    return visitList


def getDataRefList(butler, run_id, **kwargs):
    """Construct and return a list of visit IDs.

    @param: bulter (Bulter)  The data Butler
    @param: run_id (str)     The run ID
    @param: kwargs (dict):
        imageType (str)         The type of image
        testType (str or list)  The type of tests to collect visits from
        detectorName (str)      The

    @returns (list) a list of the visit IDs
    """
    testType = kwargs.get('testType', None)
    detectorName = kwargs.get('detectorName', None)
    if isinstance(testType, str):
        testTypes = [testType]
    elif isinstance(testType, list):
        testTypes = testType
    elif testType is None:
        testTypes = []
    else:
        raise TypeError("testType must be a list or str or None")

    dataId = dict(run=run_id, imageType=kwargs.get('imageType', 'BIAS'))
    if detectorName is not None:
        dataId['detectorName'] = detectorName
    dataRefList = []
    for testType in testTypes:
        dataId['testType'] = testType
        subset = butler.subset("raw", '', dataId)
        dataRefList += subset.cache
    return dataRefList


def make_file_dict(butler, runlist, varlist=None):
    """Get a set of bias and mask files out of a folder

    @param butler (Butler)    The bulter we are using
    @param runlist (list)     List of complete data IDs
    @param varlist (list)     List of variables
    """
    if varlist is None:
        varlist = ['testtype', 'visit']

    odict = {var:[] for var in varlist}

    for run in runlist:
        for var in varlist:
            if butler is None:
                value = -1
            else:
                if var in run:
                    value = run[var]
                else:
                    vallist = butler.queryMetadata('raw', var, run)
                    if len(vallist) != 1:
                        raise ValueError("Could not get %s for run %s")
                    value = vallist[0]
            odict[var].append(value)
    return odict
