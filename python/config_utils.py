"""Functions to help manage configure"""

import sys
import os
import argparse
from collections import OrderedDict

DEFAULT_ROOT_DIR = '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM/'
DEFAULT_OUT_DIR = '.'

DEFAULTS = OrderedDict(
    input=(str, None, "Input file"),
    output=(str, None, "Output file"),
    raft=(str, None, "Raft Name"),
    run=(str, None, "Run ID"),
    bias=(str, None, "Method to use for unbiasing"),
    superbias=(str, None, "Version of superbias frame to use"),
    stat=(str, "Median", "Statistic to use to stack images"),
    root_dir=(str, DEFAULT_ROOT_DIR, "Input file path root"),
    out_dir=(str, DEFAULT_OUT_DIR, "Output file path root"),
    slots=(list, None, "Slot ID(s)"),
    vmin=(float, None, "Color scale minimum value"),
    vmax=(float, None, "Color scale maximum value"),
    nbins=(int, None, "Number of bins in histogram"),
    mask=(bool, False, "Use the mask files"),
    plot=(bool, False, "Make plots"),
    std=(bool, False, "Plot standard deviation instead of mean"),
    covar=(bool, False, "Plot covarience instead of correlation factor"),
    skip=(bool, False, "Skip the main analysis and only make plots"),
    subtract_mean=(bool, False, "Subtract the mean from all images frames"),
    stats_hist=(bool, False, "Make a histogram of the distribution"),
    )


def add_arguments(parser, arg_dict):
    """Adds a set of arguments to the argument parser

    Parameters
    ----------
    parser: `argparse.ArgumentParser`
       The argument parser we are using

    arg_dict:  `collections.OrderedDict`
       The dictionary mapping argument name to (type, default, helpstring) tuple
    """
    for argname, argpars in arg_dict.items():
        argtype, argdefault, arghelp = argpars
        if argdefault is not None:
            arghelp += ": [%s]" % argdefault
        if argtype in [list]:
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



def copy_items(arg_dict, argnames):
    """Adds a set of arguments to the argument parser

    Parameters
    ----------
    arg_dict:  `collections.OrderedDict`
       The dictionary mapping argument name to (type, default, helpstring) tuple

    argnames:   list
       List of keys to copy to the output dictionary


    Returns
    -------
    outdict: `collections.OrderedDict`
       Dictionary with only the arguments we have selected
    """
    outdict = OrderedDict()
    for argname in argnames:
        if argname not in arg_dict:
            raise KeyError("Argument %s is not defined in dictionary" % argname)
        outdict[argname] = arg_dict[argname]
    return outdict



def setup_parser(argnames, arg_dict=None, **kwargs):
    """Creates an ArgumentParser and adds selected arguments

    Parameters
    ----------
    argnames:   list
       List of keys to copy to the output dictionary

    arg_dict:  `collections.OrderedDict`
       The dictionary mapping argument name to (type, default, helpstring) tuple

    Keyword arguments
    -----------------
    usage:       str
       The usage string for the ArgumentParser

    description:  str
       The description for the ArgumentParser

    *: tuple
       All other keyword arguments will be treated as addtional parameters and
       passed to the ArgumentParser

    Returns
    -------
    parser: `argparse.ArgumentParser`
       Argument parser loaded with the requested arguments
    """

    usage = kwargs.pop('usage', None)
    description = kwargs.pop('description', None)

    if arg_dict is None:
        arg_dict = DEFAULTS

    if usage is None:
        usage = "%s [options]" % os.path.basename(sys.argv[0])

    use_arg_dict = copy_items(arg_dict, argnames)
    use_arg_dict.update(**kwargs)

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description)
    add_arguments(parser, use_arg_dict)
    return parser
