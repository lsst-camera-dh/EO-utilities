#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import SLOT_FORMAT_STRING,\
    RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS

SLOT_PPUMP_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_PPUMP_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_PPUMP_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

PPUMP_DEFAULT_FIELDS = dict(testType='ppump', bias=None, superbias=None, suffix='')


RAFT_PPUMP_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_ppump_table',
                                                         RAFT_PPUMP_FORMAT_STRING,
                                                         fileType='tables',
                                                         **PPUMP_DEFAULT_FIELDS)
RAFT_PPUMP_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_ppump_plot',
                                                        RAFT_PPUMP_FORMAT_STRING,
                                                        fileType='plots',
                                                        **PPUMP_DEFAULT_FIELDS)
SLOT_PPUMP_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_ppump_table',
                                                         SLOT_PPUMP_FORMAT_STRING,
                                                         fileType='tables',
                                                         **PPUMP_DEFAULT_FIELDS)
SLOT_PPUMP_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_ppump_plot',
                                                        SLOT_PPUMP_FORMAT_STRING,
                                                        fileType='plots',
                                                        **PPUMP_DEFAULT_FIELDS)

SUM_PPUMP_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_ppump_table',
                                                        SUMMARY_PPUMP_FORMAT_STRING,
                                                        fileType='tables',
                                                        **PPUMP_DEFAULT_FIELDS)
SUM_PPUMP_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_ppump_plot',
                                                       SUMMARY_PPUMP_FORMAT_STRING,
                                                       fileType='plots',
                                                       **PPUMP_DEFAULT_FIELDS)



def get_ppump_files_run(run_id, **kwargs):
    """Get a set of ppump and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)
    hinfo = get_hardware_type_and_id(run_id)

    if acq_types is None:
        if hinfo[0] == 'LCA-11021':
            acq_types = ['ppump_raft_acq']
        else:
            acq_types = ['PPUMP']

    return get_files_for_run(run_id,
                             imagetype="PPUMP",
                             testtypes=acq_types,
                             outkey='PPUMP',
                             **kwargs)
