#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING


QE_DEFAULT_FIELDS = dict(testType='qe')


RAFT_QE_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_qe_table',
                                                      RAFT_FORMAT_STRING,
                                                      fileType='tables',
                                                      **QE_DEFAULT_FIELDS)
RAFT_QE_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_qe_plot',
                                                     RAFT_FORMAT_STRING,
                                                     fileType='plots',
                                                     **QE_DEFAULT_FIELDS)
SLOT_QE_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_qe_table',
                                                      SLOT_FORMAT_STRING,
                                                      fileType='tables',
                                                      **QE_DEFAULT_FIELDS)
SLOT_QE_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_qe_plot',
                                                     SLOT_FORMAT_STRING,
                                                     fileType='plots',
                                                     **QE_DEFAULT_FIELDS)

SUM_QE_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_qe_table',
                                                     SUMMARY_FORMAT_STRING,
                                                     fileType='tables',
                                                     **QE_DEFAULT_FIELDS)
SUM_QE_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_qe_plot',
                                                    SUMMARY_FORMAT_STRING,
                                                    fileType='plots',
                                                    **QE_DEFAULT_FIELDS)
