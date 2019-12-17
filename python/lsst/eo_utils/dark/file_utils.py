#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING,\
    SUPERDARK_FORMAT_STRING, SUPERDARK_STAT_FORMAT_STRING,\
    RUN_SUPERDARK_FORMAT_STRING, RUN_SUPERDARK_STAT_FORMAT_STRING


DARK_DEFAULT_FIELDS = dict(testType='dark')
SDARK_DEFAULT_FIELDS = dict(testType='superdark')


SUPERDARK_FORMATTER = FILENAME_FORMATS.add_format('superdark',
                                                  SUPERDARK_FORMAT_STRING)
SUPERDARK_STAT_FORMATTER = FILENAME_FORMATS.add_format('superdark_stat',
                                                       SUPERDARK_STAT_FORMAT_STRING)
RUN_SUPERDARK_FORMATTER = FILENAME_FORMATS.add_format('run_superdark',
                                                      RUN_SUPERDARK_FORMAT_STRING)
RUN_SUPERDARK_STAT_FORMATTER = FILENAME_FORMATS.add_format('run_superdark_stat',
                                                           RUN_SUPERDARK_STAT_FORMAT_STRING)

RAFT_DARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_dark_table',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **DARK_DEFAULT_FIELDS)
RAFT_DARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_dark_plot',
                                                       RAFT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **DARK_DEFAULT_FIELDS)
SLOT_DARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_dark_table',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **DARK_DEFAULT_FIELDS)
SLOT_DARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_dark_plot',
                                                       SLOT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **DARK_DEFAULT_FIELDS)

SUM_DARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_dark_table',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='tables',
                                                       **DARK_DEFAULT_FIELDS)
SUM_DARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_dark_plot',
                                                      SUMMARY_FORMAT_STRING,
                                                      fileType='plots',
                                                      **DARK_DEFAULT_FIELDS)

RAFT_SDARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_sdark_table',
                                                         RAFT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SDARK_DEFAULT_FIELDS)
RAFT_SDARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sdark_plot',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SDARK_DEFAULT_FIELDS)
SLOT_SDARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sdark_table',
                                                         SLOT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SDARK_DEFAULT_FIELDS)
SLOT_SDARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sdark_plot',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SDARK_DEFAULT_FIELDS)

SUM_SDARK_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sdark_table',
                                                        SUMMARY_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SDARK_DEFAULT_FIELDS)
SUM_SDARK_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sdark_plot',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SDARK_DEFAULT_FIELDS)
