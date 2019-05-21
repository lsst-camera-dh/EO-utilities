"""This module contains functions to find files
for qe (Quantum efficiency) analyses using the data Butler"""

from lsst.eo_utils.base.butler_utils import get_files_butler


def get_qe_files_butler(butler, run_id, **kwargs):
    """Get a set of qe frames for a run from the `Butler`

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
        testtypes = ["QE"]

    return get_files_butler(butler, run_id,
                            testtypes=testtypes,
                            imagetype="QE",
                            outkey='QE',
                            **kwargs)
