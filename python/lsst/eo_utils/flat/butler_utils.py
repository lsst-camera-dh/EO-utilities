"""This module contains functions to find files for the flat field runs
with the data `Butler`"""

from lsst.eo_utils.base.butler_utils import get_files_butler


def get_flat_files_butler(butler, run_id, **kwargs):
    """Get a set of flat-field frames for a run from the `Butler`

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
        testtypes = ["FLAT"]

    return get_files_butler(butler, run_id,
                            testtypes=testtypes,
                            imagetype="FLAT",
                            outkey='FLAT',
                            **kwargs)
