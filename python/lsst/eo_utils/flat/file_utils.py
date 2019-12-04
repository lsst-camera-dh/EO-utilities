#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING




FLAT_DEFAULT_FIELDS = dict(testType='flat')



RAFT_FLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_flat_table',
                                                        RAFT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **FLAT_DEFAULT_FIELDS)
RAFT_FLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_flat_plot',
                                                       RAFT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **FLAT_DEFAULT_FIELDS)
SLOT_FLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_flat_table',
                                                        SLOT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **FLAT_DEFAULT_FIELDS)
SLOT_FLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_flat_plot',
                                                       SLOT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **FLAT_DEFAULT_FIELDS)


SUM_FLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_flat_table',
                                                       SUMMARY_FORMAT_STRING,
                                                       fileType='tables',
                                                       **FLAT_DEFAULT_FIELDS)
SUM_FLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_flat_plot',
                                                      SUMMARY_FORMAT_STRING,
                                                      fileType='plots',
                                                      **FLAT_DEFAULT_FIELDS)
