"""This module contains functions to help manage configuration for the
offline analysis of LSST Electrical-Optical testing"""

import sys
import os
import argparse
from collections import OrderedDict

import lsst.pex.config as pexConfig


# Some default values
DEFAULT_DB = 'Dev'
DEFAULT_OUTDIR = 'analysis'
DEFAULT_STAT_TYPE = 'median'
DEFAULT_BITPIX = -32


# Some standard set of argument names
STANDARD_SLOT_ARGS = ['run', 'slots', 'butler_repo', 'outdir',
                      'plot', 'skip', 'nfiles']
STANDARD_RAFT_ARGS = ['run', 'butler_repo', 'outdir',
                      'plot', 'skip', 'nfiles']


class EOUtilConfig(pexConfig.Config):
    """A simple class to manage configuration parameters for EO analysis tasks"""
    input = pexConfig.Field("Input file", str, default=None)
    output = pexConfig.Field("Output file", str, default=None)
    logfile = pexConfig.Field("Log file", str, default="temp.log")
    batch = pexConfig.Field("Dispatch job to batch", str, default=None)
    dry_run = pexConfig.Field("Print batch command, do not send job", bool, default=False)
    batch_args = pexConfig.Field("Arguments to pass to batch command", str, default="-W 1200 -R bullet")
    run = pexConfig.Field("Run ID", str, default=None)
    slots = pexConfig.ListField("Slot ID(s)", str, default=None)
    rafts = pexConfig.ListField("Raft Slot(s)", str, default=None)
    bias = pexConfig.Field("Method to use for unbiasing", str, default=None)
    superbias = pexConfig.Field("Version of superbias frame to use", str, default=None)
    stat = pexConfig.Field("Statistic to use to stack images", str, default=None)
    butler_repo = pexConfig.Field("Butler repository", str, default=None)
    nfiles = pexConfig.Field("Number of files to use", int, default=None)
    outdir = pexConfig.Field("Output file path root", str, default=DEFAULT_OUTDIR)
    vmin = pexConfig.Field("Color scale minimum value", float, default=None)
    vmax = pexConfig.Field("Color scale maximum value", float, default=None)
    nbins = pexConfig.Field("Number of bins in histogram", int, default=100)
    mask = pexConfig.Field("Use the mask files", bool, default=False)
    plot = pexConfig.Field("Make plots", bool, default=False)
    std = pexConfig.Field("Plot standard deviation instead of mean", bool, default=False)
    covar = pexConfig.Field("Plot covarience instead of correlation factor", bool, default=False)
    skip = pexConfig.Field("Skip the main analysis and only make plots", bool, default=False)
    subtract_mean = pexConfig.Field("Subtract the mean from all images frames", bool, default=False)
    stats_hist = pexConfig.Field("Make a histogram of the distribution", bool, default=False)


    def to_odict(self):
        """@returns (dict) Parameters as an OrderedDict mapping name to (type, default, doc) tuple"""
        o_dict = OrderedDict()
        for key, val in self._fields.items():
            o_dict[key] = (val.dtype, val.default, val.__doc__)
        return o_dict


# Turn the object about into an ordered dictionary
DEFAULT_CONFIG = EOUtilConfig()
DEFAULTS = DEFAULT_CONFIG.to_odict()


def add_arguments(parser, arg_dict):
    """Adds a set of arguments to the argument parser

    @param parser (dict)    The argument parser we are using
    @param arg_dict (dict)  The dictionary mapping argument name
                            to (type, default, helpstring) tuple
    """
    for argname, argpars in arg_dict.items():
        argtype, argdefault, arghelp = argpars
        if argdefault is not None:
            arghelp += ": [%s]" % argdefault
        if argtype in [pexConfig.listField.List]:
            parser.add_argument("--%s" % argname,
                                action='append',
                                default=argdefault,
                                help=arghelp)
        elif argtype in [bool]:
            parser.add_argument("--%s" % argname,
                                action='store_true',
                                default=argdefault,
                                help=arghelp)
        else:
            parser.add_argument("--%s" % argname,
                                type=argtype,
                                default=argdefault,
                                help=arghelp)

def make_argstring(arg_dict):
    """Turns a dictionary of arguments into string with command line options

    @param arg_dict (dict)  The dictionary mapping argument name to value

    @returns (str) The corresponding string for a command line
    """
    ostring = ""
    for key, value in arg_dict.items():
        if value is None:
            continue
        elif isinstance(value, bool):
            if not value:
                continue
            else:
                ostring += " --%s" % key
        elif isinstance(value, (list, pexConfig.listField.List)):
            for vv in value:
                ostring += " --%s %s" % (key, vv)
        else:
            ostring += " --%s %s" % (key, value)
    return ostring


def copy_items(arg_dict, argnames):
    """Copy a set of parameters tuples to an smaller dictionary

    @param arg_dict (dict)  The dictionary mapping argument name to (type, default, helpstring) tuple
    @param argnames (list)  List of keys to copy to the output dictionary

    @returns (dict) Dictionary with only the arguments we have selected
    """
    outdict = OrderedDict()
    for argname in argnames:
        if argname not in arg_dict:
            raise KeyError("Argument %s is not defined in dictionary" % argname)
        outdict[argname] = arg_dict[argname]
    return outdict


def get_config_defaults(argnames, arg_dict=None, **kwargs):
    """Gets default values for selected arguments

    @param argnames (list)  List of keys to copy to the output dictionary
    @param arg_dict (dict)  The dictionary mapping argument name to (type, default, helpstring) tuple
    @param kwargs:
        All other keyword arguments will be treated as used to update the defaults

    @returns (dict) mapping parameter name to (type, default, helpstring) tuple
    """
    if arg_dict is None:
        arg_dict = DEFAULTS

    use_arg_dict = copy_items(arg_dict, argnames)
    use_arg_dict.update(**kwargs)
    return use_arg_dict


def get_config_values(argnames, arg_dict=None, **kwargs):
    """Gets default values for selected arguments

    @param argnames (list)  List of keys to copy to the output dictionary
    @param arg_dict (dict)  The dictionary mapping argument name to (type, default, helpstring) tuple
    @param kwargs:
        All other keyword arguments will be treated as used to update the values

    @returns (dict) mapping parameter name to value
    """
    defaults = get_config_defaults(argnames, arg_dict)
    outdict = {}
    for argname, argpars in defaults.items():
        outdict[argname] = argpars[1]
    outdict.update(**kwargs)
    return outdict


def setup_parser(argnames, arg_dict=None, **kwargs):
    """Creates an ArgumentParser and adds selected arguments

    @param argnames (list)  List of keys to copy to the output dictionary
    @param arg_dict (dict)  The dictionary mapping argument name to (type, default, helpstring) tuple
    @param kwargs:
        usage (str)             The usage string for the ArgumentParser
        description (str)       The description for the ArgumentParser
        All other keyword arguments will be treated as addtional
        parameters and passed to the ArgumentParser

    @returns (argparse.ArgumentParser) Argument parser loaded with the requested arguments
    """

    usage = kwargs.pop('usage', None)
    description = kwargs.pop('description', None)
    if usage is None:
        usage = "%s [options]" % os.path.basename(sys.argv[0])

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description)

    use_arg_dict = get_config_defaults(argnames, arg_dict, **kwargs)
    add_arguments(parser, use_arg_dict)
    return parser



def copy_dict(in_dict, def_dict):
    """Copy a set of key-value pairs to an new dict

    @param in_dict (dict)   The dictionary mapping argument name to (type, default, helpstring) tuple
    @param def_dict (dict)  The dictionary with the default values

    @returns (dict) Dictionary with only the arguments we have selected
    """
    outdict = { key:in_dict.get(key, val) for key, val in def_dict.items() }
    return outdict
 
