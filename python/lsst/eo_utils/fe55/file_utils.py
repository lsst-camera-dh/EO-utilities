#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

FE55_DEFAULT_FIELDS = dict(testType='fe55')


RAFT_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_fe55_table',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='tables', **FE55_DEFAULT_FIELDS)
RAFT_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_fe55_plot',
                                                       RAFT_FORMAT_STRING,
                                                       fileType='plots', **FE55_DEFAULT_FIELDS)
SLOT_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_fe55_table',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='tables', **FE55_DEFAULT_FIELDS)
SLOT_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_fe55_plot',
                                                       SLOT_FORMAT_STRING,
                                                       fileType='plots', **FE55_DEFAULT_FIELDS)
SUM_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_fe55_table',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='tables', **FE55_DEFAULT_FIELDS)
SUM_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_fe55_plot',
                                                      SUMMARY_FORMAT_STRING,
                                                      fileType='plots', **FE55_DEFAULT_FIELDS)
