#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING,\
    RUN_SUPERBIAS_FORMAT_STRING


BIAS_DEFAULT_FIELDS = dict(testType='bias')
SUPERBIAS_DEFAULT_FIELDS = dict(testType='superbias')

RAFT_BIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_bias_table',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='tables', **BIAS_DEFAULT_FIELDS)
RAFT_BIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_bias_plot',
                                                       RAFT_FORMAT_STRING,
                                                       fileType='plots', **BIAS_DEFAULT_FIELDS)
SLOT_BIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_bias_table',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='tables', **BIAS_DEFAULT_FIELDS)
SLOT_BIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_bias_plot',
                                                       SLOT_FORMAT_STRING,
                                                       fileType='plots', **BIAS_DEFAULT_FIELDS)

RUN_SUPERBIAS_FORMATTER = FILENAME_FORMATS.add_format('run_superbias',
                                                      RUN_SUPERBIAS_FORMAT_STRING)
RAFT_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_sbias_table',
                                                         RAFT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SUPERBIAS_DEFAULT_FIELDS)
RAFT_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sbias_plot',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SUPERBIAS_DEFAULT_FIELDS)
SLOT_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sbias_table',
                                                         SLOT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SUPERBIAS_DEFAULT_FIELDS)
SLOT_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sbias_plot',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SUPERBIAS_DEFAULT_FIELDS)

SUM_BIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_bias_table',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='tables', **BIAS_DEFAULT_FIELDS)
SUM_BIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_bias_plot',
                                                      SUMMARY_FORMAT_STRING,
                                                      fileType='plots', **BIAS_DEFAULT_FIELDS)
SUM_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sbias_table',
                                                        SUMMARY_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SUPERBIAS_DEFAULT_FIELDS)
SUM_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sbias_plot',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SUPERBIAS_DEFAULT_FIELDS)
