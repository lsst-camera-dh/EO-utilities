"""This module contains functions to help manage configuration for the
offline analysis of LSST Electrical-Optical testing"""

import sys
import os
import argparse
import copy

from collections import OrderedDict

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase

from .defaults import DEFAULT_OUTDIR, DEFAULT_LOGFILE,\
    DEFAULT_NBINS, DEFAULT_BATCH_ARGS, DEFAULT_BITPIX


# Some standard set of argument names
STANDARD_SLOT_ARGS = ['run', 'slots', 'butler_repo', 'outdir',
                      'plot', 'skip', 'nfiles']
STANDARD_RAFT_ARGS = ['run', 'butler_repo', 'outdir',
                      'plot', 'skip', 'nfiles']


class EOUtilOptions(pexConfig.Config):
    """A simple class to manage configuration parameters for EO analysis tasks"""

    # Options for job control
    logfile = pexConfig.Field("Log file", str,
                              default=DEFAULT_LOGFILE)
    batch = pexConfig.Field("Dispatch job to batch", str,
                            default=None)
    dry_run = pexConfig.Field("Print batch command, do not send job", bool,
                              default=False)
    batch_args = pexConfig.Field("Arguments to pass to batch command", str,
                                 default=DEFAULT_BATCH_ARGS)

    # Options for the data source
    butler_repo = pexConfig.Field("Butler repository", str, default=None)

    # Options for selecing input data
    dataset = pexConfig.Field("dataset", str, default=None)
    run = pexConfig.Field("Run ID", str, default=None)
    runs = pexConfig.ListField("Run IDs", str, default=None)
    slot = pexConfig.Field("Slot ID", str, default=None)
    slots = pexConfig.ListField("Slot ID(s)", str, default=None)
    raft = pexConfig.Field("Raft Slot", str, default=None)
    rafts = pexConfig.ListField("Raft Slot(s)", str, default=None)
    nfiles = pexConfig.Field("Number of files to use", int, default=None)
    insuffix = pexConfig.Field("Suffix for input files", str, default="")

    # Options for input data processing
    bias = pexConfig.Field("Method to use for unbiasing", str, default=None)
    superbias = pexConfig.Field("Version of superbias frame to use", str,
                                default=None)
    mask = pexConfig.Field("Use the mask files", bool, default=False)

    # Options for where to put output data and what to include
    outdir = pexConfig.Field("Output file path root", str,
                             default=DEFAULT_OUTDIR)
    outsuffix = pexConfig.Field("Suffix for output files", str,
                                default="")
    plot = pexConfig.Field("Make plots", str,
                           default=None)
    skip = pexConfig.Field("Skip the main analysis and only make plots", bool,
                           default=False)

    # Options for what to compute
    std = pexConfig.Field("Plot standard deviation instead of mean", bool,
                          default=False)
    covar = pexConfig.Field("Plot covarience instead of correlation factor", bool,
                            default=False)
    stat = pexConfig.Field("Statistic to use to stack images", str,
                           default=None)
    subtract_mean = pexConfig.Field("Subtract the mean from all images frames", bool,
                                    default=False)

    # Plotting options
    stats_hist = pexConfig.Field("Make a histogram of the distribution", bool,
                                 default=False)
    vmin = pexConfig.Field("Color scale minimum value", float,
                           default=None)
    vmax = pexConfig.Field("Color scale maximum value", float,
                           default=None)
    nbins = pexConfig.Field("Number of bins in histogram", int,
                            default=DEFAULT_NBINS)
    subtract_mean = pexConfig.Field("Subtract the mean from all images frames", bool,
                                    default=False)

    # Other output options
    bitpix = pexConfig.Field("FITS bitpix value", int, default=DEFAULT_BITPIX)

    # Options for Fe55 Tasks
    use_all = pexConfig.Field("Use all fe55 clusters", bool, default=False)


    @classmethod
    def clone_param(cls, par_name, **kwargs):
        """
        @param par_name       Parameter to clone
        @param kwargs:
            default          Set the default value for the cloned version

        @returns (`pexConfig.Field`) cloned version of parameter
        """
        ret_val = copy.deepcopy(cls.__dict__[par_name])
        if 'default' in kwargs:
            ret_val.default = kwargs['default']
        return ret_val


def add_pex_arguments(parser, pex_class, exclude=None):
    """Adds a set of arguments to the argument parser (or parser group)

    @param parser (`argumentParser`)   The argument parser we are using
    @param pex_class (`pexConfig`)     The configuration class we are using to fill the parser
    @param exclude (list)              Name of parameters to exclude
    """
    if exclude is None:
        exclude = []
    for key, val in pex_class._fields.items():
        if key in exclude:
            continue
        if isinstance(val, pexConfig.listField.ListField):
            parser.add_argument("--%s" % key,
                                action='append',
                                type=val.itemtype,
                                default=val.default,
                                help=val.doc)
        elif val.dtype in [bool]:
            parser.add_argument("--%s" % key,
                                action='store_true',
                                default=val.default,
                                help=val.doc)
        else:
            parser.add_argument("--%s" % key,
                                type=val.dtype,
                                default=val.default,
                                help=val.doc)


def make_argstring(**kwargs):
    """Turns a dictionary of arguments into string with command line options

    @param arg_dict (dict)  The dictionary mapping argument name to value

    @returns (str) The corresponding string for a command line
    """
    ostring = ""
    for key, value in kwargs.items():
        if value is None:
            continue
        elif isinstance(value, bool):
            if not value:
                continue
            else:
                ostring += " --%s" % key
        elif isinstance(value, (list, pexConfig.listField.List)):
            for val2 in value:
                ostring += " --%s %s" % (key, val2)
        else:
            ostring += " --%s %s" % (key, value)
    return ostring


def copy_items(arg_dict, argnames):
    """Copy a set of parameters tuples to an smaller dictionary

    @param arg_dict (dict)  The dictionary mapping name to (type, default, helpstring) tuple
    @param argnames (list)  List of keys to copy to the output dictionary

    @returns (dict) Dictionary with only the arguments we have selected
    """
    outdict = OrderedDict()
    for argname in argnames:
        if argname not in arg_dict:
            raise KeyError("Argument %s is not defined in dictionary" % argname)
        outdict[argname] = arg_dict[argname]
    return outdict



def setup_parser(**kwargs):
    """Creates an ArgumentParser and adds selected arguments

    @param argnames (list)  List of keys to copy to the output dictionary
    @param arg_dict (dict)  The dictionary mapping name to (type, default, helpstring) tuple
    @param kwargs:
        usage (str)             The usage string for the ArgumentParser
                                All other keyword arguments will passed to the ArgumentParser c'tor

    @returns (`argparse.ArgumentParser`) Argument parser loaded with the requested arguments
    """

    usage = kwargs.pop('usage', None)
    if usage is None:
        usage = "%s [options]" % os.path.basename(sys.argv[0])

    parser = argparse.ArgumentParser(usage=usage, *kwargs)

    return parser



def copy_dict(in_dict, def_dict):
    """Copy a set of key-value pairs to an new dict

    @param in_dict (dict)   The dictionary with the input values
    @param def_dict (dict)  The dictionary with the default values

    @returns (dict) Dictionary with only the arguments we have selected
    """
    outdict = {key:in_dict.get(key, val) for key, val in def_dict.items()}
    return outdict


def copy_pex_fields(field_names, target_class, library_class):
    """Copy a set of pexConfig.Field objects to a target class

    This is a way to make sure that all config classes in this
    package are using the same pexConfig.Field object and
    share the same parameters when appropriate

    @param field_names (list)                 : Name of parameters to copy
    @param target_class (`pexConfig.Config`)  : Class to add parameters to
    @param library_class (`pexConfig.Config`) : Class to copy parameters from
    """
    for fname in field_names:
        try:
            item = library_class.__dict__[fname]
        except KeyError:
            raise KeyError("Field %s does not exist in class %s\n" % (fname, type(library_class)))
        if isinstance(item, pexConfig.Field):
            setattr(target_class, fname, copy.deepcopy(item))
        else:
            raise TypeError("Field %s in class %s\n is not a pexConfig.Field" %
                            (fname, type(library_class)))



class Configurable(pipeBase.Task):
    """A small interface on top of `pipeBase.Task` to make
    it easier to handle configuration from various sources
    """
    _DefaultName = "Configurable"

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        super(Configurable, self).__init__()
        self.safe_update(**kwargs)

    def safe_update(self, **kwargs):
        """ C'tor
        Update the configuration from a set of kw

        @returns (dict)   The key, val pairs not in the configuration class
        """
        base_dict = self.config.toDict()
        update_dict = {}
        remain_dict = {}
        for key, val in kwargs.items():
            if key in base_dict:
                update_dict[key] = val
            else:
                remain_dict[key] = val
        self.config.update(**update_dict)
        return remain_dict


    def extract_config_vals(self, def_dict):
        """ C'tor
        Extract a set of configuration values to a dict

        @param def_dict (dict)     Dictionary with the default values

        @returns (dict)            Dictionary with the output values
        """
        return copy_dict(self.config.toDict(), def_dict)
