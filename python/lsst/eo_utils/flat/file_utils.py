#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import SLOT_FORMAT_STRING,\
    RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS



SLOT_FLAT_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_FLAT_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_FLAT_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

FLAT_DEFAULT_FIELDS = dict(testType='flat', bias=None, superbias=None, suffix='')



RAFT_FLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_flat_table',
                                                        RAFT_FLAT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **FLAT_DEFAULT_FIELDS)
RAFT_FLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_flat_plot',
                                                       RAFT_FLAT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **FLAT_DEFAULT_FIELDS)
SLOT_FLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_flat_table',
                                                        SLOT_FLAT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **FLAT_DEFAULT_FIELDS)
SLOT_FLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_flat_plot',
                                                       SLOT_FLAT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **FLAT_DEFAULT_FIELDS)


SUM_FLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_flat_table',
                                                       SUMMARY_FLAT_FORMAT_STRING,
                                                       fileType='tables',
                                                       **FLAT_DEFAULT_FIELDS)
SUM_FLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_flat_plot',
                                                      SUMMARY_FLAT_FORMAT_STRING,
                                                      fileType='plots',
                                                      **FLAT_DEFAULT_FIELDS)


def get_flat_files_run(run_id, **kwargs):
    """Get a set of flat and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)
    hinfo = get_hardware_type_and_id(run_id)

    if acq_types is None:
        if hinfo[0] == 'LCA-11021':
            acq_types = ['flat_pair_raft_acq']
        else:
            acq_types = ['FLAT']

    return get_files_for_run(run_id,
                             imagetype="FLAT",
                             testtypes=acq_types,
                             outkey='FLAT',
                             **kwargs)
