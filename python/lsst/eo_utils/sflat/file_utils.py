#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING,\
    SUPERFLAT_FORMAT_STRING, SUPERFLAT_STAT_FORMAT_STRING, RUN_SUPERFLAT_FORMAT_STRING,\
    SUPERFLAT_SPEC_FORMAT_STRING, get_hardware_type_and_id, get_files_for_run


SFLAT_DEFAULT_FIELDS = dict(testType='sflat')

SUPERFLAT_FORMATTER = FILENAME_FORMATS.add_format('superflat',
                                                  SUPERFLAT_FORMAT_STRING)
SUPERFLAT_SPEC_FORMATTER = FILENAME_FORMATS.add_format('superflat_spec',
                                                       SUPERFLAT_SPEC_FORMAT_STRING)
SUPERFLAT_STAT_FORMATTER = FILENAME_FORMATS.add_format('superflat_stat',
                                                       SUPERFLAT_STAT_FORMAT_STRING)
RUN_SUPERFLAT_FORMATTER = FILENAME_FORMATS.add_format('run_superflat',
                                                      RUN_SUPERFLAT_FORMAT_STRING)

RAFT_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_sflat_table',
                                                         RAFT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SFLAT_DEFAULT_FIELDS)
RAFT_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sflat_plot',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SFLAT_DEFAULT_FIELDS)
SLOT_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sflat_table',
                                                         SLOT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SFLAT_DEFAULT_FIELDS)
SLOT_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sflat_plot',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SFLAT_DEFAULT_FIELDS)

SUM_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sflat_table',
                                                        SUMMARY_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SFLAT_DEFAULT_FIELDS)
SUM_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sflat_plot',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SFLAT_DEFAULT_FIELDS)

def get_sflat_files_run(run_id, **kwargs):
    """Get a set of sflat and mask files out of a folder

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
            testtypes = ['sflat_raft_acq']
            #testtypes = ['SFLAT']
            imagetype = "SFLAT"
        else:
            testtypes = ['SFLAT']
            imagetype = "FLAT"

    return get_files_for_run(run_id,
                             imagetype=imagetype,
                             testtypes=testtypes,
                             outkey='SFLAT',
                             **kwargs)
