#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type using the data Butler"""

import os

from lsst.daf.persistence import Bulter


BIAS_TEST_TYPES = ["DARK", "FE55"]

MASK_TYPES_DEFAULT = ['fe55_raft_analysis',
                      'dark_defects_raft',
                      'traps_raft',
                      'bright_defects_raft']

BUTLER_TS8_REPO = '/gpfs/slac/lsst/fs1/u/echarles/DATA/butler_test/repo_RTM-004-Dev'
BUTLER_BOT_REPO = ''

BUTLER_REPO_DICT = dict(TS8=BUTLER_TS8_REPO,
                        BOT=BULTER_BOT_REPO)

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
        visitList += bulter.queryMetadata("raw", 'visit', dataId)
    return visitList
        
                      
    
