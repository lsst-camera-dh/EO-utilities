"""This module contains provides an interface to get files that works either with or without Butler"""

import sys

from .defaults import DEFAULT_DATA_SOURCE, DEFAULT_TESTSTAND

from .butler_utils import get_files_butler

from .file_utils import get_files_for_run



class DataLocationInfo:
    """Object to collect information about were to find data for a particular test
    """
    def __init__(self, imagetype, **kwargs):
        """C'tor

        Parameters
        ----------
        imagetype : `str`
            The type of image, also the default name

        Keywords
        --------
        All keywords are used to override particular locations

        For example:
        if test_name is 'Flat' and the keyword ts8_butler_testtype='SFlat'
        This will return 'Flat' for all names except `ts8_butler_testtype`
        """
        self._imagetype = imagetype
        self._name_dict = kwargs.copy()

    @property
    def imagetype(self):
        """Return the type of image used for these tests"""
        return self._imagetype

    def __getitem__(self, key):
        """Returns a particular item by key, defaults to self._imagetype"""
        return self._name_dict.get(key, self._imagetype)

    def get_trait(self, traitname, **kwargs):
        """Returns the name of an particular trait for a
        given data access method and teststand

        Parameters
        ----------
        traitname : `str`
            The trait we want e.g., 'imagetype' or 'testname'

        Keywords
        --------
        teststand : `str`
            The teststand ( 'ts8' | 'bot )
        data_source : `str`
            The data source ( 'glob' | 'datacat' | 'butler' | 'butler_file' )

        Returns
        -------
        ret_val : `str`
            The value for this trait
        """
        teststand = kwargs.get('teststand', DEFAULT_TESTSTAND)
        data_source = kwargs.get('data_source', DEFAULT_DATA_SOURCE)
        if teststand in ['bot_etu']:
            teststand = 'bot'
        if data_source in ['butler', 'butler_files']:
            data_source = 'butler'

        key = '%s_%s_%s' % (teststand, data_source, traitname)
        return self[key]


    def get_testname(self, **kwargs):
        """Returns the string used as a key for this test type
        given data access method and teststand

        Keywords
        --------
        teststand : `str`
            The teststand ( 'ts8' | 'bot )
        data_source : `str`
            The data source ( 'glob' | 'datacat' | 'butler' | 'butler_file' )

        Returns
        -------
        ret_val : `str`
            The test type
        """
        return self.get_trait('testname', **kwargs)

    def get_imagetype(self, **kwargs):
        """Returns the string used as a key for this image type
        given data access method and teststand

        Keywords
        --------
        teststand : `str`
            The teststand ( 'ts8' | 'bot )
        data_source : `str`
            The data source ( 'glob' | 'datacat' | 'butler' | 'butler_file' )

        Returns
        -------
        ret_val : `str`
            The image type
        """
        return self.get_trait('imagetype', **kwargs)


BIAS_LOCATION_INFO = DataLocationInfo('bias',
                                      ts8_glob_testname='bias_raft_acq',
                                      ts8_glob_imagetype='bias_bias',
                                      bot_glob_imagetype='bias_bias')
DARK_LOCATION_INFO = DataLocationInfo('dark',
                                      ts8_glob_testname='dark_raft_acq',
                                      ts8_glob_imagetype='dark_dark')
FLAT_LOCATION_INFO = DataLocationInfo('flat',
                                      ts8_glob_testname='flat_pair_raft_acq',
                                      ts8_glob_imagetype=['flat1', 'flat2'],
                                      bot_glob_imagetype=['flat1', 'flat2'])
FE55_LOCATION_INFO = DataLocationInfo('fe55',
                                      ts8_glob_testname='fe55_raft_acq',
                                      bot_glob_imagetype='flat_*_flat',
                                      bot_butler_testname='FE55_FLAT')
PPUMP_LOCATION_INFO = DataLocationInfo('ppump',
                                       ts8_glob_testname='ppump_raft_acq',
                                       ts8_butler_testname='TRAP',
                                       bot_butler_testname='TRAP')
SFLAT_LOCATION_INFO = DataLocationInfo('sflat',
                                       ts8_glob_testname='sflat_raft_acq',
                                       ts8_butler_testname='SFLAT_500',
                                       bot_glob_imagetype='FLAT',
                                       bot_butler_imagetype='FLAT',
                                       ts8_butler_imagetype='FLAT')
QE_LOCATION_INFO = DataLocationInfo('lambda',
                                    ts8_glob_testname='qe_raft_acq',
                                    bot_glob_imagetype='FLAT',
                                    ts8_glob_imagetype='FLAT',
                                    bot_butler_imagetype='FLAT',
                                    ts8_butler_imagetype='FLAT')
LOCATION_INFO_DICT = dict(BIAS=BIAS_LOCATION_INFO,
                          DARK=DARK_LOCATION_INFO,
                          FLAT=FLAT_LOCATION_INFO,
                          FE55=FE55_LOCATION_INFO,
                          PPUMP=PPUMP_LOCATION_INFO,
                          SFLAT=SFLAT_LOCATION_INFO,
                          QE=QE_LOCATION_INFO)

TEST_TYPES = ['BIAS', 'DARK', 'FLAT', 'FE55', 'PPUMP', 'SFLAT', 'QE']


def get_data_for_run(butler, run_id, **kwargs):
    """Builds a dictionary of filenames or butler dataids for
    a particular run and test type, given a data access method, teststand

    Parameters
    ----------
    butler : `Butler` or `None`
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
        Dictionary mapping raft:slot:imagetype to lists of filenames
    """
    kwcopy = kwargs.copy()
    teststand = kwcopy.get('teststand', DEFAULT_TESTSTAND)
    data_source = kwcopy.get('data_source', DEFAULT_DATA_SOURCE)
    imagetype = kwcopy.pop('imagetype', None)
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


    if testtypes is None:
        testtypes = TEST_TYPES

    testnames = []
    for testtype in testtypes:
        try:
            testnames.append(LOCATION_INFO_DICT[testtype].get_testname(teststand=teststand,
                                                                       data_source=data_source))
        except KeyError:
            raise KeyError("Did not find testtype %s" % testtype)

    retval = None

    if data_source in ['butler', 'butler_file']:
        retval = get_files_butler(butler, run_id,
                                  imagetype=imagetype.upper(),
                                  testtypes=testnames,
                                  **kwcopy)
    elif data_source in ['glob', 'datacat']:
        retval = get_files_for_run(run_id,
                                   imagetype=imagetype,
                                   testtypes=testnames,
                                   **kwcopy)
    else:
        raise ValueError("Unknown data_source (%s)" % data_source)

    if not retval:
        raise ValueError("Call to get_data_for_run returned no data")
    return retval
