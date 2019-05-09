#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import DATACAT_TS8_TEST_TYPES, DATACAT_BOT_TEST_TYPES

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS, SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

from lsst.eo_utils.bias.file_utils import get_bias_suffix

SLOT_FE55_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_FE55_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_FE55_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

FE55_DEFAULT_FIELDS = dict(testType='fe55', bias=None, superbias=None, suffix='')


RAFT_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_fe55_table',
                                                        RAFT_FE55_FORMAT_STRING,
                                                        fileType='tables', **FE55_DEFAULT_FIELDS)
RAFT_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_fe55_plot',
                                                       RAFT_FE55_FORMAT_STRING,
                                                       fileType='plots', **FE55_DEFAULT_FIELDS)
SLOT_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_fe55_table',
                                                        SLOT_FE55_FORMAT_STRING,
                                                        fileType='tables', **FE55_DEFAULT_FIELDS)
SLOT_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_fe55_plot',
                                                       SLOT_FE55_FORMAT_STRING,
                                                       fileType='plots', **FE55_DEFAULT_FIELDS)
SUM_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_fe55_table',
                                                       SUMMARY_FE55_FORMAT_STRING,
                                                       fileType='tables', **FE55_DEFAULT_FIELDS)
SUM_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_fe55_plot',
                                                      SUMMARY_FE55_FORMAT_STRING,
                                                      fileType='plots', **FE55_DEFAULT_FIELDS)


def fe55_suffix(**kwargs):
    """Return the suffix for a fe55 analysis file

    @param caller ('Task')  Object calling this function
    @param kwargs:          Passed to get_raft_file_basename

    @returns (str)          The suffix.
    """
    suffix = get_bias_suffix(**kwargs)
    if kwargs.get('use_all', False):
        suffix = '_all%s' % suffix
    else:
        suffix = '_good%s' % suffix
    return suffix


def get_fe55_files_run(run_id, **kwargs):
    """Get a set of fe55 and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)
    hinfo = get_hardware_type_and_id(run_id)

    if acq_types is None:
        if hinfo[0] == 'LCA-11021':
            acq_types = DATACAT_TS8_TEST_TYPES
        else:
            acq_types = DATACAT_BOT_TEST_TYPES

    return get_files_for_run(run_id,
                             imageType="FE55",
                             testTypes=acq_types,
                             outkey='FE55',
                             **kwargs)
