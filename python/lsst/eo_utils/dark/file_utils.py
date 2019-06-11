#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS, SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

SUPERDARK_FORMAT_STRING =\
    '{outdir}/superdark/{raft}/{raft}-{run}-{slot}_superdark_b-{bias}_s-{superbias}{suffix}.fits'
SUPERDARK_STAT_FORMAT_STRING =\
    '{outdir}/superdark/{raft}/{raft}-{run}-{slot}_{stat}_b-{bias}_s-{superbias}{suffix}.fits'

SLOT_DARK_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_DARK_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_DARK_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

DARK_DEFAULT_FIELDS = dict(testType='dark', bias=None, superbias=None, suffix='')

SLOT_SDARK_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_SDARK_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_SDARK_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

SDARK_DEFAULT_FIELDS = dict(testType='superdark', bias=None, superbias=None, suffix='')


SUPERDARK_FORMATTER = FILENAME_FORMATS.add_format('superdark',
                                                  SUPERDARK_FORMAT_STRING,
                                                  bias=None, superbias=None, suffix='')
SUPERDARK_STAT_FORMATTER = FILENAME_FORMATS.add_format('superdark_stat',
                                                       SUPERDARK_STAT_FORMAT_STRING,
                                                       bias=None, superbias=None, suffix='')

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

RAFT_SDARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_sdark_table',
                                                         RAFT_SDARK_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SDARK_DEFAULT_FIELDS)
RAFT_SDARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sdark_plot',
                                                        RAFT_SDARK_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SDARK_DEFAULT_FIELDS)
SLOT_SDARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sdark_table',
                                                         SLOT_SDARK_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SDARK_DEFAULT_FIELDS)
SLOT_SDARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sdark_plot',
                                                        SLOT_SDARK_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SDARK_DEFAULT_FIELDS)

SUM_SDARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sdark_table',
                                                        SUMMARY_SDARK_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SDARK_DEFAULT_FIELDS)
SUM_SDARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sdark_plot',
                                                       SUMMARY_SDARK_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SDARK_DEFAULT_FIELDS)


def get_dark_files_run(run_id, **kwargs):
    """Get a set of dark and mask files out of a folder

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
            testtypes = ['dark_raft_acq']
            imagetype = 'DARK_DARK'
        else:
            testtypes = ['DARK']
            imagetype = 'DARK'

    return get_files_for_run(run_id,
                             imagetype=imagetype,
                             testtypes=testtypes,
                             outkey='DARK',
                             **kwargs)
