#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS, SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

SUPERFLAT_FORMAT_STRING =\
    '{outdir}/superflat/{raft}/{raft}-{run}-{slot}_superflat_b-{bias_type}{suffix}.fits'
SUPERFLAT_STAT_FORMAT_STRING =\
    '{outdir}/superflat/{raft}/{raft}-{run}-{slot}_{stat_type}_b-{bias_type}{suffix}.fits'

SLOT_SFLAT_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_SFLAT_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_SFLAT_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

SFLAT_DEFAULT_FIELDS = dict(testType='sflat', bias=None, superbias=None, suffix='')

SUPERFLAT_FORMATTER = FILENAME_FORMATS.add_format('superflat',
                                                  SUPERFLAT_FORMAT_STRING,
                                                  bias_type=None, suffix='')
SUPERFLAT_STAT_FORMATTER = FILENAME_FORMATS.add_format('superflat_stat',
                                                       SUPERFLAT_STAT_FORMAT_STRING,
                                                       bias_type=None, suffix='')

RAFT_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_sflat_table',
                                                         RAFT_SFLAT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SFLAT_DEFAULT_FIELDS)
RAFT_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sflat_plot',
                                                        RAFT_SFLAT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SFLAT_DEFAULT_FIELDS)
SLOT_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sflat_table',
                                                         SLOT_SFLAT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SFLAT_DEFAULT_FIELDS)
SLOT_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sflat_plot',
                                                        SLOT_SFLAT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SFLAT_DEFAULT_FIELDS)

SUM_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sflat_table',
                                                        SUMMARY_SFLAT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SFLAT_DEFAULT_FIELDS)
SUM_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sflat_plot',
                                                       SUMMARY_SFLAT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SFLAT_DEFAULT_FIELDS)



def get_sflat_files_run(run_id, **kwargs):
    """Get a set of sflat and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)
    hinfo = get_hardware_type_and_id(run_id)

    if acq_types is None:
        if hinfo[0] == 'LCA-11021':
            acq_types = ['sflat_raft_acq']
        else:
            acq_types = ['SFLAT']

    return get_files_for_run(run_id,
                             imagetype="SFLAT",
                             testtypes=acq_types,
                             outkey='SFLAT',
                             **kwargs)
