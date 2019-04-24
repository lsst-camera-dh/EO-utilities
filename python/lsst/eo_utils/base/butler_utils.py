"""This module contains functions to find files of a particular type using the data Butler"""

from lsst.daf.persistence import Butler

from .defaults import BUTLER_REPO_DICT


def get_butler_by_repo(repo, **kwargs):
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
    rafts = butler.queryMetadata('raw', 'raftname', dict(run=run_num))
    if len(rafts) > 1:
        htype = 'LCA-10134'
        hid = 'LCA-10134-0001'
    else:
        htype = 'LCA-11021'
        hid = rafts[0]
    return (htype, hid)


def get_raft_names_butler(butler, run_num):
    """Return the list of rafts from a given run

    @param: butler (Bulter)  The data Butler
    @param run_num(str)      The number number we are reading

    @returns (list) the raft names for that run
    """
    rafts = butler.queryMetadata('raw', 'raftname', dict(run=run_num))
    return rafts


def get_visit_list(butler, run_id, **kwargs):
    """Construct and return a list of visit IDs.

    @param: bulter (Bulter)  The data Butler
    @param: run_id (str)     The run ID
    @param: kwargs (dict):
        imagetype (str)         The type of image, e.g., BIAS or DARK or FLAT
        testtype (str or list)  The type of tests to collect visits from

    @returns (list) a list of the visit IDs
    """

    testtype = kwargs.get('testtype', None)
    if isinstance(testtype, str):
        testtypes = [testtype]
    elif isinstance(testtype, list):
        testtypes = testtype
    elif testtype is None:
        testtypes = []
    else:
        raise TypeError("testtype must be a list or str or None")

    data_id = dict(run=run_id, imagetype=kwargs.get('imagetype', 'BIAS'))
    visit_list = []
    for testtype in testtypes:
        data_id['testtype'] = testtype
        visit_list += butler.queryMetadata("raw", 'visit', data_id)
    return visit_list


def get_data_ref_list(butler, run_id, **kwargs):
    """Construct and return a list of data_ids.

    @param: bulter (Bulter)  The data Butler
    @param: run_id (str)     The run ID
    @param: kwargs (dict):
        imagetype (str)         The type of image, e.g., BIAS or DARK or FLAT
        testtype (str or list)  The type of tests to collect visits from
        detectorname (str)      The name of the slot, e.g., S00, S11, ...
        nfiles (int)            Number of files per test to use, default is to use all

    @returns (list) a list of the visit IDs
    """
    testtype = kwargs.get('testtype', None)
    detectorname = kwargs.get('detectorname', None)
    raftname = kwargs.get('raftname', None)
    nfiles = kwargs.get('nfiles', None)

    if isinstance(testtype, str):
        testtypes = [testtype]
    elif isinstance(testtype, list):
        testtypes = testtype
    elif testtype is None:
        testtypes = []
    else:
        raise TypeError("testtype must be a list or str or None")

    data_id = dict(run=run_id, imagetype=kwargs.get('imagetype', 'BIAS'))
    if detectorname is not None:
        data_id['detectorname'] = detectorname
    if raftname is not None:
        data_id['raftname'] = raftname

    data_ref_list = []
    for testtype in testtypes:
        data_id['testtype'] = testtype
        subset = butler.subset("raw", '', data_id)
        if nfiles is None:
            data_ref_list += subset.cache
        else:
            data_ref_list += subset.cache[0:min(nfiles, len(subset.cache))]
    return data_ref_list


def make_file_dict(butler, runlist, varlist=None):
    """Get a set of data_ids of the Butler and sort them into a dictionary

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
       testtypes (list)         The types of acquistions we want to include
       imagetype (str)          The image type we want
       nfiles (int)             Number of files per test to use
       outkey (str)             Where to put the output file
       nfiles (int)             Number of files to include per test

    @returns (dict)          Dictionary mapping the data_ids from raft, slot, and file type
    """
    testtypes = kwargs.get('testtypes')
    imagetype = kwargs.get('imagetype')
    nfiles = kwargs.get('nfiles', None)
    rafts = kwargs.get('rafts', None)
    outkey = kwargs.get('outkey', imagetype)

    outdict = {}
    if rafts is None:
        rafts = butler.queryMetadata('raw', 'raftname', dict(run=run_id, imagetype=imagetype))

    bias_kwargs = dict(imagetype=imagetype, testtype=testtypes, nfiles=nfiles)
    for raft in rafts:
        bias_kwargs['raftname'] = raft
        if raft not in outdict:
            outdict[raft] = {}

        slots = butler.queryMetadata('raw', 'detectorname', dict(run=run_id,
                                                                 imagetype=imagetype,
                                                                 raftname=raft))

        for slot in slots:
            bias_kwargs['detectorname'] = slot
            outdict[raft][slot] = {outkey:get_data_ref_list(butler, run_id, **bias_kwargs)}

    return outdict
