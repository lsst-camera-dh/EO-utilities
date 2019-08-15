#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

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
