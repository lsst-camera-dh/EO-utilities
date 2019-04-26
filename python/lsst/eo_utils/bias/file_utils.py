#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import DATACAT_TS8_TEST_TYPES, DATACAT_BOT_TEST_TYPES,\
     SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS

SUPERBIAS_STAT_FORMAT_STRING =\
    '{outdir}/superbias/{raft}/{raft}-{run}-{slot}_{stat_type}_b-{bias_type}{suffix}.fits'
SLOT_BIAS_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_BIAS_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_BIAS_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')

BIAS_DEFAULT_FIELDS = dict(testType='bias', bias=None, superbias=None, suffix='')
SUPERBIAS_DEFAULT_FIELDS = dict(testType='superbias', bias=None, superbias=None, suffix='')


SUPERBIAS_STAT_FORMATTER = FILENAME_FORMATS.add_format('superbias_stat',
                                                       SUPERBIAS_STAT_FORMAT_STRING,
                                                       bias_type=None, suffix='')

RAFT_BIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_bias_table',
                                                        RAFT_BIAS_FORMAT_STRING,
                                                        fileType='tables', **BIAS_DEFAULT_FIELDS)
RAFT_BIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_bias_plot',
                                                       RAFT_BIAS_FORMAT_STRING,
                                                       fileType='plots', **BIAS_DEFAULT_FIELDS)
SLOT_BIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_bias_table',
                                                        SLOT_BIAS_FORMAT_STRING,
                                                        fileType='tables', **BIAS_DEFAULT_FIELDS)
SLOT_BIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_bias_plot',
                                                       SLOT_BIAS_FORMAT_STRING,
                                                       fileType='plots', **BIAS_DEFAULT_FIELDS)

RAFT_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('raft_sbias_table',
                                                         RAFT_BIAS_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SUPERBIAS_DEFAULT_FIELDS)
RAFT_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sbias_plot',
                                                        RAFT_BIAS_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SUPERBIAS_DEFAULT_FIELDS)
SLOT_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sbias_table',
                                                         SLOT_BIAS_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SUPERBIAS_DEFAULT_FIELDS)
SLOT_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sbias_plot',
                                                        SLOT_BIAS_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SUPERBIAS_DEFAULT_FIELDS)

SUM_BIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_bias_table',
                                                       SUMMARY_BIAS_FORMAT_STRING,
                                                       fileType='tables', **BIAS_DEFAULT_FIELDS)
SUM_BIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_bias_plot',
                                                      SUMMARY_BIAS_FORMAT_STRING,
                                                      fileType='plots', **BIAS_DEFAULT_FIELDS)
SUM_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sbias_table',
                                                        SUMMARY_BIAS_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SUPERBIAS_DEFAULT_FIELDS)
SUM_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sbias_plot',
                                                       SUMMARY_BIAS_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SUPERBIAS_DEFAULT_FIELDS)



def get_bias_suffix(**kwargs):
    """Return the suffix for bias files

    @param kwargs (dict)
        bias_type(str)
        superbias_type(str)
        stat (str)
        std (bool)
        suffix (str)

    the format is _b-{bias_type}_s-{superbias_type}{stat}{suffix}
    @return (str) the suffix
    """
    bias_type = kwargs.get('bias', None)
    superbias_type = kwargs.get('superbias', None)
    kwsuffix = kwargs.get('suffix', None)
    stat_type = kwargs.get('stat', None)

    suffix = ""
    if bias_type is None:
        suffix += "_b-none"
    else:
        suffix += "_b-%s" % bias_type

    if superbias_type is None:
        suffix += "_s-none"
    else:
        suffix += "_s-%s" % superbias_type

    if kwargs.get('std', False):
        suffix += "_std"

    if stat_type is not None:
        suffix += "_%s" % stat_type

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix


def get_superbias_suffix(**kwargs):
    """Return the suffix for bias files

    @param kwargs (dict)
        superbias_type(str)
        std (bool)
        suffix (str)
        stat (str)

    the format is b-{superbias_type}{stat}{suffix}
    @return (str) the suffix
    """
    superbias_type = kwargs.get('superbias', None)
    stat_type = kwargs.get('stat', None)
    kwsuffix = kwargs.get('suffix', None)
    suffix = ""

    if superbias_type is None:
        suffix += "_b-none"
    else:
        suffix += "_b-%s" % (superbias_type)

    if kwargs.get('std', False):
        suffix += "_std"

    if stat_type is not None:
        suffix += "_%s" % stat_type

    if kwsuffix is not None:
        suffix += "_%s" % kwsuffix
    return suffix


def get_bias_files_run(run_id, **kwargs):
    """Get a set of bias and mask files out of a folder

    @param run_id (str)      The number number we are reading
    @param kwargs
       acq_types (list)  The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    acq_types = kwargs.get('acq_types', None)
    hinfo = get_hardware_type_and_id(run_id)

    if acq_types is None:
        if hinfo[0] == 'LCA-11021':
            acq_types = DATACAT_TS8_TEST_TYPES
        else:
            acq_types = DATACAT_BOT_TEST_TYPES

    return get_files_for_run(run_id,
                             imagetype="BIAS",
                             testtypes=acq_types,
                             outkey='BIAS',
                             **kwargs)
