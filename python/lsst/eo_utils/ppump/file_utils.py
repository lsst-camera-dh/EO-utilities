#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING


PPUMP_DEFAULT_FIELDS = dict(testType='ppump')


RAFT_PPUMP_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_ppump_table',
                                                         RAFT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **PPUMP_DEFAULT_FIELDS)
RAFT_PPUMP_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_ppump_plot',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **PPUMP_DEFAULT_FIELDS)
SLOT_PPUMP_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_ppump_table',
                                                         SLOT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **PPUMP_DEFAULT_FIELDS)
SLOT_PPUMP_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_ppump_plot',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **PPUMP_DEFAULT_FIELDS)

SUM_PPUMP_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_ppump_table',
                                                        SUMMARY_FORMAT_STRING,
                                                        fileType='tables',
                                                        **PPUMP_DEFAULT_FIELDS)
SUM_PPUMP_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_ppump_plot',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='plots',
                                                       **PPUMP_DEFAULT_FIELDS)
