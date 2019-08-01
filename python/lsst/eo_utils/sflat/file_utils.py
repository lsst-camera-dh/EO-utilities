#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

SUPERFLAT_FORMAT_STRING =\
    '{outdir}/{teststand}/superflat/{raft}/{raft}-{run}-{slot}_superflat_b-{bias}_s-{superbias}{suffix}_l'
SUPERFLAT_STAT_FORMAT_STRING =\
    '{outdir}/{teststand}/superflat/{raft}/{raft}-{run}-{slot}_{stat}_b-{bias}_s-{superbias}{suffix}_l'

SLOT_SFLAT_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_SFLAT_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_SFLAT_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

SFLAT_DEFAULT_FIELDS = dict(testType='sflat', bias=None, superbias=None, suffix='')

SUPERFLAT_FORMATTER = FILENAME_FORMATS.add_format('superflat',
                                                  SUPERFLAT_FORMAT_STRING,
                                                  bias=None, superbias=None, suffix='')
SUPERFLAT_STAT_FORMATTER = FILENAME_FORMATS.add_format('superflat_stat',
                                                       SUPERFLAT_STAT_FORMAT_STRING,
                                                       bias=None, superbias=None, suffix='')

RAFT_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_sflat_table',
                                                         RAFT_SFLAT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SFLAT_DEFAULT_FIELDS)
RAFT_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sflat_plot',
                                                        RAFT_SFLAT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SFLAT_DEFAULT_FIELDS)
SLOT_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sflat_table',
                                                         SLOT_SFLAT_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SFLAT_DEFAULT_FIELDS)
SLOT_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sflat_plot',
                                                        SLOT_SFLAT_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SFLAT_DEFAULT_FIELDS)

SUM_SFLAT_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sflat_table',
                                                        SUMMARY_SFLAT_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SFLAT_DEFAULT_FIELDS)
SUM_SFLAT_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sflat_plot',
                                                       SUMMARY_SFLAT_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SFLAT_DEFAULT_FIELDS)
