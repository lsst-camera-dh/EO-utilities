#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

from lsst.eo_utils.bias.file_utils import get_bias_suffix

SLOT_FE55_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_FE55_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_FE55_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

FE55_DEFAULT_FIELDS = dict(testType='fe55', bias=None, superbias=None, suffix='')


RAFT_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_fe55_table',
                                                        RAFT_FE55_FORMAT_STRING,
                                                        fileType='tables', **FE55_DEFAULT_FIELDS)
RAFT_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_fe55_plot',
                                                       RAFT_FE55_FORMAT_STRING,
                                                       fileType='plots', **FE55_DEFAULT_FIELDS)
SLOT_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_fe55_table',
                                                        SLOT_FE55_FORMAT_STRING,
                                                        fileType='tables', **FE55_DEFAULT_FIELDS)
SLOT_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_fe55_plot',
                                                       SLOT_FE55_FORMAT_STRING,
                                                       fileType='plots', **FE55_DEFAULT_FIELDS)
SUM_FE55_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_fe55_table',
                                                       SUMMARY_FE55_FORMAT_STRING,
                                                       fileType='tables', **FE55_DEFAULT_FIELDS)
SUM_FE55_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_fe55_plot',
                                                      SUMMARY_FE55_FORMAT_STRING,
                                                      fileType='plots', **FE55_DEFAULT_FIELDS)


def fe55_suffix(**kwargs):
    """Return the suffix for a fe55 analysis file

    Keywords
    --------
    bias : `str`
        Type of unbiasing to use
    superbias : `str`
        Type of superbias frame to use
    use_all : `bool`
        Flag to use all clusters in the analysis

    Returns
    -------
    suffix : `str`
        The suffix.
    """
    suffix = get_bias_suffix(**kwargs)
    if kwargs.get('use_all', False):
        suffix = '_all%s' % suffix
    else:
        suffix = '_good%s' % suffix
    return suffix
