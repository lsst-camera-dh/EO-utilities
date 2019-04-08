"""This module contains functions to find files of a particular type using the data Butler"""

from lsst.daf.persistence import Butler


# This is the location of the Teststand 8 runs at SLAC
BUTLER_TS8_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/ts8'
# This is the location of the BOT runs at SLAC
BUTLER_BOT_REPO = '/gpfs/slac/lsst/fs3/g/data/datasets/bot'

# Map the Butler repos to simple names
BUTLER_REPO_DICT = dict(TS8=BUTLER_TS8_REPO,
                        BOT=BUTLER_BOT_REPO)


# FIXME, we should get this from a single place
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
    """Return the hardware type and hardware id for a given run

    @param: butler (Bulter)  The data Butler
    @param run_num(str)      The number number we are reading

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
        imageType (str)         The type of image, e.g., BIAS or DARK or FLAT
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
    """Construct and return a list of dataIds.

    @param: bulter (Bulter)  The data Butler
    @param: run_id (str)     The run ID
    @param: kwargs (dict):
        imageType (str)         The type of image, e.g., BIAS or DARK or FLAT
        testType (str or list)  The type of tests to collect visits from
        detectorName (str)      The name of the slot, e.g., S00, S11, ...
        nfiles (int)            Number of files per test to use, default is to use all

    @returns (list) a list of the visit IDs
    """
    testType = kwargs.get('testType', None)
    detectorName = kwargs.get('detectorName', None)
    raftName = kwargs.get('raftName', None)
    nfiles = kwargs.get('nfiles', None)

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
    if raftName is not None:
        dataId['raftName'] = raftName

    dataRefList = []
    for testType in testTypes:
        dataId['testType'] = testType
        subset = butler.subset("raw", '', dataId)
        if nfiles is None:
            dataRefList += subset.cache
        else:
            dataRefList += subset.cache[0:min(nfiles, len(subset.cache))]
    return dataRefList


def make_file_dict(butler, runlist, varlist=None):
    """Get a set of dataIds of the Butler and sort them into a dictionary

    @param butler (Butler)    The bulter we are using
    @param runlist (list)     List of complete dataIDs
    @param varlist (list)     List of variables values to use as keys for the output dictionary

    @returns (dict)           A dictionary of dataIDs, 
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



def get_files_butler(butler, run_id, **kwargs):
    """Get a set of files out of a folder

    @param butler (Butler)   The bulter we are using
    @param run_id (str)      The number number we are reading
    @param kwargs
       rafts (str)              The rafts we want data for
       testTypes (list)         The types of acquistions we want to include
       imageType (str)          The image type we want
       nfiles (int)             Number of files per test to use
       outkey (str)             Where to put the output file
       nfiles (int)             Number of files to include per test

    @returns (dict)          Dictionary mapping the dataIds from raft, slot, and file type
    """
    testTypes = kwargs.get('testTypes')
    imageType = kwargs.get('imageType')
    nfiles = kwargs.get('nfiles', None)
    rafts = kwargs.get('rafts', None)
    outkey = kwargs.get('outkey', imageType)

    outdict = {}
    if rafts is None:
        rafts = butler.queryMetadata('raw', 'raftName', dict(run=run_id, imageType=imageType))

    bias_kwargs = dict(imageType=imageType, testType=testTypes, nfiles=nfiles)
    for raft in rafts:
        bias_kwargs['raftName'] = raft
        if raft not in outdict:
            outdict[raft] = {}

        slots = butler.queryMetadata('raw', 'detectorName', dict(run=run_id,
                                                                 imageType=imageType,
                                                                 raftName=raft))

        for slot in slots:
            bias_kwargs['detectorName'] = slot
            outdict[raft][slot] = {outkey:getDataRefList(butler, run_id, **bias_kwargs)}

    return outdict
