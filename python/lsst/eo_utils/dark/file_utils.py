#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import SLOT_FORMAT_STRING,\
    RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS

SLOT_DARK_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_DARK_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_DARK_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

DARK_DEFAULT_FIELDS = dict(testType='dark', bias=None, superbias=None, suffix='')


RAFT_DARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_dark_table',
                                                        RAFT_DARK_FORMAT_STRING,
                                                        fileType='tables',
                                                        **DARK_DEFAULT_FIELDS)
RAFT_DARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_dark_plot',
                                                       RAFT_DARK_FORMAT_STRING,
                                                       fileType='plots',
                                                       **DARK_DEFAULT_FIELDS)
SLOT_DARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_dark_table',
                                                        SLOT_DARK_FORMAT_STRING,
                                                        fileType='tables',
                                                        **DARK_DEFAULT_FIELDS)
SLOT_DARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_dark_plot',
                                                       SLOT_DARK_FORMAT_STRING,
                                                       fileType='plots',
                                                       **DARK_DEFAULT_FIELDS)

SUM_DARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_dark_table',
                                                       SUMMARY_DARK_FORMAT_STRING,
                                                       fileType='tables',
                                                       **DARK_DEFAULT_FIELDS)
SUM_DARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_dark_plot',
                                                      SUMMARY_DARK_FORMAT_STRING,
                                                      fileType='plots',
                                                      **DARK_DEFAULT_FIELDS)



def get_dark_files_run(run_id, **kwargs):
    """Get a set of dark and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)
    hinfo = get_hardware_type_and_id(run_id)

    if acq_types is None:
        if hinfo[0] == 'LCA-11021':
            acq_types = ['dark_raft_acq']
        else:
            acq_types = ['DARK']

    return get_files_for_run(run_id,
                             imagetype="DARK",
                             testtypes=acq_types,
                             outkey='DARK',
                             **kwargs)
