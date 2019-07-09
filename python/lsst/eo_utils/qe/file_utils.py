#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id,\
    get_files_for_run, merge_file_dicts,\
    FILENAME_FORMATS, SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

SLOT_QE_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_QE_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_QE_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

QE_DEFAULT_FIELDS = dict(testType='qe', bias=None, superbias=None, suffix='')


RAFT_QE_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_qe_table',
                                                      RAFT_QE_FORMAT_STRING,
                                                      fileType='tables',
                                                      **QE_DEFAULT_FIELDS)
RAFT_QE_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_qe_plot',
                                                     RAFT_QE_FORMAT_STRING,
                                                     fileType='plots',
                                                     **QE_DEFAULT_FIELDS)
SLOT_QE_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_qe_table',
                                                      SLOT_QE_FORMAT_STRING,
                                                      fileType='tables',
                                                      **QE_DEFAULT_FIELDS)
SLOT_QE_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_qe_plot',
                                                     SLOT_QE_FORMAT_STRING,
                                                     fileType='plots',
                                                     **QE_DEFAULT_FIELDS)

SUM_QE_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_qe_table',
                                                     SUMMARY_QE_FORMAT_STRING,
                                                     fileType='tables',
                                                     **QE_DEFAULT_FIELDS)
SUM_QE_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_qe_plot',
                                                    SUMMARY_QE_FORMAT_STRING,
                                                    fileType='plots',
                                                    **QE_DEFAULT_FIELDS)



def get_qe_files_run(run_id, **kwargs):
    """Get a set of qe and mask files out of a folder

    Parameters
    ----------
    run_id : `str`
        The number number we are reading
    kwargs
        Passed along to the underlying get_files_for_run function

    Returns
    -------
    outdict : `dict`
        Dictionary mapping slot to file names
    """
    testtypes = kwargs.get('testtypes', None)
    hinfo = get_hardware_type_and_id(run_id)

    if testtypes is None:
        if hinfo[0] == 'LCA-11021':
            testtypes = ['qe_raft_acq']
        else:
            testtypes = ['QE']

    lambda_dict = get_files_for_run(run_id,
                                    imagetype="flat",
                                    testtypes=testtypes,
                                    outkey='LAMBDA',
                                    **kwargs)
    bias_dict = get_files_for_run(run_id,
                                  imagetype="bias",
                                  testtypes=testtypes,
                                  outkey='BIAS',
                                  **kwargs)

    return merge_file_dicts(lambda_dict, bias_dict)
