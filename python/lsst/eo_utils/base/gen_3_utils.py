"""This module contains functions to find files of a particular type using the data Butler"""

from lsst.daf.bulter import Butler

from .defaults import BUTLER_REPO_DICT

RAW_COLS = ['LSSTCam/raw/all']

def get_butler_by_repo(repo, **kwargs):
    """Construct and return a Bulter for the requested repository

    Parameters
    ----------
    repo : `str`
        Name of the repo, e.g., 'TS8' | 'BOT'
    kwargs
        Passed to the Bulter constructor

    Returns
    -------
    butler : `Butler`
        the requested Bulter

    Raises
    ------
    KeyError : If repo does not match any known repository
    """
    try:
        repo_path = BUTLER_REPO_DICT[repo]
    except KeyError:
        raise KeyError("Unknown Bulter repo key %s" % repo)
    butler = Butler(repo_path, collections=RAW_COLS, **kwargs)
    return butler


def get_filename_from_id(butler, data_id):
    """Return the hardware type and hardware id for a given run

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    data_id : `dict`
        The data id in question

    Returns
    -------
    filename : `str`
        The filename for the assocated CCD data
    """
    return butler.getURIs("raw", collections=RAW_COLS, data_id)[0].path


def get_hardware_info(butler, run_num):
    """Return the hardware type and hardware id for a given run

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    run_num : `str`
        The number number we are reading

    Returns
    -------
    htype : `str`
        The hardware type, either 'LCA-10134' (aka full camera) or
        'LCA-11021' (single raft)
    hid : `str`
        The hardware id, e.g., RMT-004
    """
    rafts = get_raft_names_butler(butler, run_num)
    if len(rafts) > 1:
        htype = 'LCA-10134'
        hid = 'LCA-10134-0001'
    else:
        htype = 'LCA-11021'
        hid = rafts[0]
    return (htype, hid)


def get_raft_names_butler(butler, run):
    """Return the list of rafts from a given run

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    run : `str`
        The number number we are reading

    Returns
    -------
    rafts : lists
        The raft names for that run
    """
    sqlline = "instrument='LSSTCam' AND exposure.science_program='%s'" % run    
    refs = list(butler.registry.queryDatasets("raw", collections=RAW_COLS, where=sqlline)
    rafts = np.unique([butler.registry.expandDataId(ref.dataId).records['detector'].raft for ref in refs])
    return rafts


def get_slot_names_butler(butler, run, raft):
    """Return the list of rafts from a given run

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    run : `str`
        The number number we are reading
    raft : `str`
        The raft 

    Returns
    -------
    slots : list
        The slot names for that raft and run
    """
    sqlline = "instrument='LSSTCam' AND exposure.science_program='%s' AND detector.raft='%s'" % (run, raft)
    refs = list(butler.registry.queryDatasets("raw", collections=RAW_COLS, where=sqlline)
    slots = np.unique([butler.registry.expandDataId(ref.dataId).records['detector'].name_in_raft for ref in refs])
    return slots


def get_visit_list(butler, run, **kwargs):
    """Construct and return a list of visit IDs.

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    run : `str`
        The number number we are reading

    Keywords
    --------
    imagetype : `str`
        The type of image, e.g., BIAS or DARK or FLAT
    testtype : `str` or `list`
        The type of tests to collect visits from

    Returns
    -------
    visit_list : list
        A list of the visit IDs
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

    data_id = dict(run=run, imagetype=kwargs.get('imagetype', 'BIAS'))
    visit_list = []
    for testtype in testtypes:
        sqlline = "instrument='LSSTCam' AND exposure.science_program='%s' AND exposure.observation_reason='%s'" % (run, testtype)
        visit_list += butler.queryDataIds("exposure", collections=RAW_COLS, where=sqlline)
    return visit_list


def get_data_ref_list(butler, run, **kwargs):
    """Construct and return a list of data_ids.

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    run : `str`
        The number number we are reading

    Keywords
    --------
    imagetype : `str`
        The type of image, e.g., BIAS or DARK or FLAT
    testtype : `str` or `list`
        The type of tests to collect visits from
    detectorname : `str`
        The name of the slot, e.g., S00, S11, ...
    nfiles : `int`
        Number of files per test to use, default is to use all

    Returns
    -------
    data_ref_list : `list`
        List of the visit IDs
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

    data_id = dict(run=run, imagetype=kwargs.get('imagetype', 'BIAS'))
    if detectorname is not None:
        data_id['detectorname'] = detectorname
    if raftname is not None:
        data_id['raftname'] = raftname

    sqlline_base = "instrument='LSSTCam' AND exposure.science_program='%s' AND exposure.observation_type='%s'" %\
                    (run, imagetype=kwargs.get('imagetype', 'bias')
        
    data_ref_list = []
    for testtype in testtypes:
        data_id['testtype'] = testtype.upper()
        
        sqlline = sqlline_base + " AND exposure.observation_reason='%s'" % testtype
        if detectorname is not None:
            sqlline += " AND detector.name_in_raft='%s'" % detectorname
        if raftname is not None:
            sqlline += " AND detector.raft='%s'" % raftname
        
        data_ids = butler.registry.queryDatasets("raw", collections=['LSSTCam/raw/all'], where=sqlline)
        idx = np.argsort([ref.dataId['exposure'] for ref in data_ids])
        if nfiles is None:
            data_ref_list += data_ids[idx]
        else:
            data_ref_list += data_ids[idx][0:min(nfiles, len(subset.cache))]
    return data_ref_list


def get_files_butler(butler, run_id, **kwargs):
    """Get a set of files out of a folder

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    run_id : `str`
        The number number we are reading

    Keywords
    --------
    rafts : `str` or `list`
        The raft or rafts we want data for
    imagetype : `str`
        The type of image, e.g., BIAS or DARK or FLAT
    testtypes : `list`
        The type of tests to collect visits from
    detectorname : `str`
        The name of the slot, e.g., S00, S11, ...
    nfiles : `int`
        Number of files per test to use, default is to use all
    outkey : `str`
        Key to use in the output dictionary


    Returns
    -------
    out_dict : `dict`
        Dictionary mapping the data_ids from raft, slot, and file type
    """
    testtypes = kwargs.get('testtypes')
    imagetype = kwargs.get('imagetype')
    nfiles = kwargs.get('nfiles', None)
    rafts = kwargs.get('rafts', None)
    slots = kwargs.get('slots', None)
    outkey = kwargs.get('outkey', imagetype)

    outdict = {}
    if rafts is None:
        rafts = get_raft_names_butler(butler, run_id)

    bias_kwargs = dict(imagetype=imagetype, testtype=testtypes, nfiles=nfiles)
    for raft in rafts:
        bias_kwargs['raftname'] = raft
        if raft not in outdict:
            outdict[raft] = {}

        if slots is None:
            slots = get_slot_names_butler(butler, run_id, raft)

        for slot in slots:
            bias_kwargs['detectorname'] = slot
            outdict[raft][slot] = {outkey:get_data_ref_list(butler, run_id, **bias_kwargs)}

    return outdict
