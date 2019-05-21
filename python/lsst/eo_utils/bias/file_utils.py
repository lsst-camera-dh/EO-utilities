#!/usr/bin/env python

# -*- python -*-

"""This module contains functions to find files of a particular type in the SLAC directory tree"""

from lsst.eo_utils.base.defaults import DATACAT_TS8_TEST_TYPES, DATACAT_BOT_TEST_TYPES

from lsst.eo_utils.base.file_utils import get_hardware_type_and_id, get_files_for_run,\
    FILENAME_FORMATS, SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING

SLOT_BIAS_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
RAFT_BIAS_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SUMMARY_BIAS_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_b-{bias}_s-{superbias}_{suffix}')
SLOT_SBIAS_FORMAT_STRING =\
    SLOT_FORMAT_STRING.replace('{suffix}', '_{stat}_s-{superbias}_{suffix}')
RAFT_SBIAS_FORMAT_STRING =\
    RAFT_FORMAT_STRING.replace('{suffix}', '_{stat}_s-{superbias}_{suffix}')
SUMMARY_SBIAS_FORMAT_STRING =\
    SUMMARY_FORMAT_STRING.replace('{suffix}', '_{stat}_s-{superbias}_{suffix}')

BIAS_DEFAULT_FIELDS = dict(testType='bias', bias=None, superbias=None, suffix='')
SUPERBIAS_DEFAULT_FIELDS = dict(testType='superbias', superbias=None, suffix='')


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
                                                         RAFT_SBIAS_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SUPERBIAS_DEFAULT_FIELDS)
RAFT_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('raft_sbias_plot',
                                                        RAFT_SBIAS_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SUPERBIAS_DEFAULT_FIELDS)
SLOT_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('slot_sbias_table',
                                                         SLOT_SBIAS_FORMAT_STRING,
                                                         fileType='tables',
                                                         **SUPERBIAS_DEFAULT_FIELDS)
SLOT_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('slot_sbias_plot',
                                                        SLOT_SBIAS_FORMAT_STRING,
                                                        fileType='plots',
                                                        **SUPERBIAS_DEFAULT_FIELDS)

SUM_BIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_bias_table',
                                                       SUMMARY_BIAS_FORMAT_STRING,
                                                       fileType='tables', **BIAS_DEFAULT_FIELDS)
SUM_BIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_bias_plot',
                                                      SUMMARY_BIAS_FORMAT_STRING,
                                                      fileType='plots', **BIAS_DEFAULT_FIELDS)
SUM_SBIAS_TABLE_FORMATTER = FILENAME_FORMATS.add_format('sum_sbias_table',
                                                        SUMMARY_SBIAS_FORMAT_STRING,
                                                        fileType='tables',
                                                        **SUPERBIAS_DEFAULT_FIELDS)
SUM_SBIAS_PLOT_FORMATTER = FILENAME_FORMATS.add_format('sum_sbias_plot',
                                                       SUMMARY_SBIAS_FORMAT_STRING,
                                                       fileType='plots',
                                                       **SUPERBIAS_DEFAULT_FIELDS)



def get_bias_suffix(**kwargs):
    """Return the suffix for bias files

    the format is _b-{bias_type}_s-{superbias_type}{stat}{suffix}

    Parameters
    ----------
    kwargs
        Passed to formatting statement

    Returns
    -------
    suffix : `str`
        The suffix
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

    the format is b-{superbias_type}{stat}{suffix}

    Parameters
    ----------
    kwargs
        Passed to formatting statement

    Returns
    -------
    suffix : `str`
        The suffix
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

    Parameters
    ----------
    run_id : `str`
        The number number we are reading
    kwargs
        Passed along to the underlying get_files_for_run function

    Returns
    -------
    outdict : `dict`
        Dictionary mapping slot to file names
    """
    testtypes = kwargs.get('testtypes', None)
    hinfo = get_hardware_type_and_id(run_id)
    if testtypes is None:
        if hinfo[0] == 'LCA-11021':
            testtypes = DATACAT_TS8_TEST_TYPES
        else:
            testtypes = DATACAT_BOT_TEST_TYPES

    return get_files_for_run(run_id,
                             imagetype="BIAS",
                             testtypes=testtypes,
                             outkey='BIAS',
                             **kwargs)
