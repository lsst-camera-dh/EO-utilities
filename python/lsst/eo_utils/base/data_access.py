"""This module contains provides an interface to get files that works either with or without Butler"""

import sys

from .defaults import DEFAULT_DATA_SOURCE, DEFAULT_TESTSTAND

from .butler_utils import get_files_butler

from .file_utils import get_files_for_run


TEST_TYPES = ['DARK', 'FLAT', 'FE55', 'PPUMP', 'SFLAT', 'LAMBDA']

TS8_BUTLER_NAMES = dict(DARK='DARK',
                        FLAT='FLAT',
                        FE55='FE55',
                        PPUMP='PPUMP',
                        SFLAT='SFLAT',
                        LAMBDA='LAMBDA')
TS8_DATACAT_NAMES = dict(DARK='DARK',
                         FLAT='FLAT',
                         FE55='FE55',
                         PPUMP='PPUMP',
                         SFLAT='SFLAT',
                         LAMBDA='LAMBDA')
TS8_GLOB_NAMES = dict(DARK='dark_raft_acq',
                      FLAT='flat_pair_raft_acq',
                      FE55='fe55_raft_acq',
                      PPUMP='ppump_raft_acq',
                      SFLAT='sflat_raft_acq',
                      LAMBDA='qe_raft_acq')

BOT_BUTLER_NAMES = dict(DARK='DARK',
                        FLAT='FLAT',
                        FE55='FE55',
                        PPUMP='PPUMP',
                        SFLAT='SFLAT',
                        LAMBDA='LAMBDA')
BOT_DATACAT_NAMES = dict(DARK='DARK',
                         FLAT='FLAT',
                         FE55='FE55',
                         PPUMP='PPUMP',
                         SFLAT='SFLAT',
                         LAMBDA='LAMBDA')
BOT_GLOB_NAMES = dict(DARK='dark',
                      FLAT='flat',
                      FE55='fe55',
                      PPUMP='ppump',
                      SFLAT='sflat',
                      LAMBDA='lambda')

TS8_TEST_NAMES = dict(glob=TS8_GLOB_NAMES,
                      datacat=TS8_DATACAT_NAMES,
                      butler=TS8_BUTLER_NAMES)
BOT_TEST_NAMES = dict(glob=BOT_GLOB_NAMES,
                      datacat=BOT_DATACAT_NAMES,
                      butler=BOT_BUTLER_NAMES)

DATA_TEST_TYPES = dict(ts8=TS8_TEST_NAMES,
                       bot=BOT_TEST_NAMES,
                       bot_etu=BOT_TEST_NAMES)


def get_data_for_run(butler, run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    Parameters
    ----------
    butler : `Bulter` or `None`
        The data Butler
    run_id : `str`
        The number number we are reading

    Keywords
    --------
    teststand : `str`
        The name of the teststand, used to find data
    data_source : `str`
        Flag that determines how to find data
    testtypes : `list` or `None`
        List of the types of tests to accept data for
    logger : `Logger` or `None`
        Log stream
    Other keywords are passed along to the underlying get_files_for_run function

    Returns
    -------
    outdict : `dict`
        Dictionary mapping slot to file names
    """
    kwcopy = kwargs.copy()
    teststand = kwcopy.get('teststand', DEFAULT_TESTSTAND)
    data_source = kwcopy.get('data_source', DEFAULT_DATA_SOURCE)
    testtypes = kwcopy.pop('testtypes', None)
    logger = kwcopy.get('log', None)

    if data_source in ['butler', 'butler_file']:
        if butler is None:
            raise ValueError("data_source='%s', but not Butler was provided" % data_source)
    else:
        if butler is not None:
            if logger is None:
                sys.stdout.write("Warning, data_source='%s', but a Butler was provided.\n" % data_source)
            else:
                logger.warning("Warning, data_source='%s', but a Butler was provided." % data_source)

    try:
        test_name_dict = DATA_TEST_TYPES[teststand][data_source]
    except KeyError as msg:
        raise KeyError("Could not find test types for test_stand=%s data_soure=%s, %s" %\
                           (teststand, data_source, msg))

    if testtypes is None:
        testtypes = TEST_TYPES

    testtypes = [test_name_dict[key] for key in testtypes]

    retval = None
    if data_source in ['butler', 'butler_file']:
        retval = get_files_butler(butler, run_id,
                                  testtypes=testtypes,
                                  **kwcopy)
    elif data_source in ['glob', 'datacat']:
        retval = get_files_for_run(run_id,
                                   testtypes=testtypes,
                                   **kwcopy)
    else:
        raise ValueError("Unknown data_source (%s)" % data_source)

    if not retval:
        raise ValueError("Call to get_data_for_run returned no data")
    return retval
