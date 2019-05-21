"""This module contains functions to find files
for bias analyses using the data Butler"""

from lsst.eo_utils.base.defaults import BUTLER_TEST_TYPES
from lsst.eo_utils.base.butler_utils import get_files_butler


def get_bias_files_butler(butler, run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    Parameters
    ----------
    butler : `Bulter`
        The data Butler
    run_id : `str`
        The number number we are reading

    Returns
    -------
    out_dict : `dict`
        Dictionary mapping the data_ids from raft, slot, and file type
    """
    testtypes = kwargs.get('testtypes', None)

    if testtypes is None:
        testtypes = BUTLER_TEST_TYPES

    return get_files_butler(butler, run_id,
                            testtypes=testtypes,
                            imagetype='BIAS',
                            outkey='BIAS',
                            **kwargs)
