"""This module contains functions to find files of a particular type using the data Butler"""

from lsst.eo_utils.base.butler_utils import get_files_butler

BIAS_TEST_TYPES = ['DARK', 'FLAT', 'FE55', 'PPUMP', 'SFLAT', 'LAMBDA', 'TRAP']


def get_bias_files_butler(butler, run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param butler (`Butler`)    The bulter we are using
    @param run_id (str)         The run number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include
                         The remaining kwargs are passed to get_files_butler

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)

    if acq_types is None:
        acq_types = BIAS_TEST_TYPES

    return get_files_butler(butler, run_id,
                            testTypes=acq_types,
                            imageType="BIAS",
                            outkey='BIAS',
                            **kwargs)
