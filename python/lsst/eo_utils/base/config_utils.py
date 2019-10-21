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
    DEFAULT_NBINS, DEFAULT_BATCH_ARGS, DEFAULT_BITPIX,\
    DEFAULT_DATA_SOURCE, DEFAULT_TESTSTAND




class EOUtilOptions(pexConfig.Config):
    """Library of configurate parameters used by eo_utils tasks

    The are all here to ensure that different task with the same parameters
    actually used exactly the same parameters.

    Various task configuration classes should use the clone_param() method to
    copy any of the parameters they need from this library class.
    """

    # Options for job control
    logfile = pexConfig.Field("Log file", str,
                              default=DEFAULT_LOGFILE)
    batch = pexConfig.Field("Dispatch job to batch", str,
                            default=None)
    nofail = pexConfig.Field("Continue if a job fails", bool,
                             default=False)
    dry_run = pexConfig.Field("Print batch command, do not send job", bool,
                              default=False)
    batch_args = pexConfig.Field("Arguments to pass to batch command", str,
                                 default=DEFAULT_BATCH_ARGS)

    # Options for the data source
    data_source = pexConfig.Field("Data Source (glob | datacat | butler | butler_file)", str,
                                  default=DEFAULT_DATA_SOURCE)
    teststand = pexConfig.Field("Teststand name (ts8 | bot | bot_etu)", str,
                                default=DEFAULT_TESTSTAND)

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
    infile = pexConfig.Field("Input file name", str, default=None)
    indir = pexConfig.Field("Input directory name", str, default=DEFAULT_OUTDIR)
    outfile = pexConfig.Field("Output file name", str, default=None)

    # Options for input data processing
    bias = pexConfig.Field("Method to use for unbiasing", str, default='spline')
    superbias = pexConfig.Field("Version of superbias frame to use", str,
                                default='spline')
    gain = pexConfig.Field("Use the gain correction", bool, default=False)
    mask = pexConfig.Field("Use the mask files", bool, default=False)
    nonlin = pexConfig.Field("Use the nonlinearity correction", bool, default=False)

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
    mosaic = pexConfig.Field("Plot a raft- or ccd-level mosaic", bool,
                             default=False)

    # Other output options
    bitpix = pexConfig.Field("FITS bitpix value", int, default=DEFAULT_BITPIX)

    # Options for Fe55 Tasks
    use_all = pexConfig.Field("Use all fe55 clusters", bool, default=False)

    # Options for Flat Tasks
    smoothing = pexConfig.Field("Smoothing for spline overscan correction", int, default=11000)
    minflux = pexConfig.Field("Minimum flux for overscan fitting.", float, default=10000.0)
    maxflux = pexConfig.Field("Maximum flux for overscan fitting.", float, default=140000.0)
    num_oscan_pixels = pexConfig.Field("Number of overscan pixels used for model fit.",
                                       int, default=10)

    # Options for BF Tasks
    maxLag = pexConfig.Field("Max lag for BF analysis", int, default=1)
    nSigmaClip = pexConfig.Field("Sigma clip for BF analysis", int, default=3)
    backgroundBinSize = pexConfig.Field("Background bin size for BF analysis", int, default=128)

    # Options for CTE Tasks
    overscans = pexConfig.Field("Number of overscan rows/columns to use", int, default=2)
    nframes = pexConfig.Field("Number of frames used to make superflat", int, default=5)

    # Options for Trap Tasks
    cycles = pexConfig.Field("Trap cycles", int, default=100)
    threshold = pexConfig.Field("Trap threshold", float, default=200.)
    C2_thresh = pexConfig.Field("C2 threshold", float, default=10.)
    C3_thresh = pexConfig.Field("C3 threshold", float, default=1.)
    bkg_nx = pexConfig.Field("Local background width (pixels)", int, default=10)
    bkg_ny = pexConfig.Field("Local background height (pixels)", int, default=10)
    edge_rolloff = pexConfig.Field("Edge rolloff width (pixels)", int, default=10)

    # Options for html reports
    template_file = pexConfig.Field("HTML report template file", str, default=None)
    htmldir = pexConfig.Field("HTML report directory", str,
                              default=os.path.join(DEFAULT_OUTDIR, 'html'))
    css_file = pexConfig.Field("HTML report style file", str, default=None)
    plot_report_action = pexConfig.Field("How to deal with figures in repots", str,
                                         default='link')

    @classmethod
    def clone_param(cls, par_name, **kwargs):
        """Clone a parameter from the set defined in this class.

        Parameters
        ----------
        par_name : `str`
            Parameter to clone
        kwargs
            default : `str`           Set the default value for the cloned version

        Returns
        -------
        ret_val : `pexConfig.Field`
            cloned version of parameter
        """
        ret_val = copy.deepcopy(cls.__dict__[par_name])
        if 'default' in kwargs:
            ret_val.default = kwargs['default']
        return ret_val

    @staticmethod
    def task_param(task_class):
        """Build parameter from for a particular Task

        Parameters
        ----------
        task_class : `class`
            Class of task of build parameter for

        Returns
        -------
        ret_val : `pexConfig.ConfigurableField`
            Parameter connect to the task class
        """
        param = pexConfig.ConfigurableField(target=task_class,
                                            doc=task_class.__doc__)
        return param



def add_pex_arguments(parser, pex_class, exclude=None, prefix=None):
    """Adds a set of arguments to the argument parser (or parser group)

    Parameters
    ----------
    parser : `argumentParser`
        The argument parser we are using
    pex_class : `pexConfig`
        The configuration class we are using to fill the parser
    exclude : `list`
        Names of parameters to exclude
    """
    if exclude is None:
        exclude = []

    for key, val in pex_class._fields.items():
        if key in exclude:
            continue
        if prefix is not None:
            parser_key = "%s.%s" % (prefix, key)
        else:
            parser_key = key
        if isinstance(val, pexConfig.listField.ListField):
            parser.add_argument("--%s" % parser_key,
                                action='append',
                                type=val.itemtype,
                                default=val.default,
                                help=val.doc)
        elif isinstance(val, pexConfig.configurableField.ConfigurableField):
            parser_group = parser.add_argument_group(val.name)
            add_pex_arguments(parser_group, val.default, exclude, val.name)
        elif val.dtype in [bool]:
            parser.add_argument("--%s" % parser_key,
                                action='store_true',
                                default=val.default,
                                help=val.doc)
        else:
            parser.add_argument("--%s" % parser_key,
                                type=val.dtype,
                                default=val.default,
                                help=val.doc)


def make_argstring(config, **kwargs):
    """Turns a dictionary of arguments into string with command line options

    Parameters
    ----------
    config
        The configuration (used to get defaults)

    kwargs
        The dictionary mapping argument name to value


    Returns
    -------
    ostring : `str`
        The corresponding string for a command line
    """
    ostring = ""
    for key, value in kwargs.items():
        try:
            def_value = config._fields[key].default
        except KeyError:
            def_value = None
        if value in [def_value, None]:
            continue
        if isinstance(value, bool):
            if not value:
                continue
            ostring += " --%s" % key
        elif isinstance(value, str):
            if not value:
                continue
            ostring += " --%s %s" % (key, value)
        elif isinstance(value, (list, pexConfig.listField.List)):
            for val2 in value:
                ostring += " --%s %s" % (key, val2)
        elif isinstance(value, (dict)):
            for key2, val2 in value.items():
                ostring += " --%s.%s %s" % (key, key2, val2)
        else:
            ostring += " --%s %s" % (key, value)
    return ostring


def copy_items(arg_dict, argnames):
    """Copy a set of parameters tuples to an smaller dictionary

    Parameters
    ----------
    arg_dict : `dict`
        The dictionary mapping name to (type, default, helpstring) tuple
    argnames : `list`
        List of keys to copy to the output dictionary

    Returns
    -------
    outdict : `dict`
        Dictionary with only the arguments we have selected
    """
    outdict = OrderedDict()
    for argname in argnames:
        if argname not in arg_dict:
            raise KeyError("Argument %s is not defined in dictionary" % argname)
        outdict[argname] = arg_dict[argname]
    return outdict



def setup_parser(**kwargs):
    """Creates an ArgumentParser and adds selected arguments

    Keywords
    --------
    usage : `str`
        The usage string for the ArgumentParser
        All other keyword arguments will passed to the ArgumentParser c'tor

    Returns
    -------
    parser : `argparse.ArgumentParser`
        Argument parser loaded with the requested arguments
    """

    usage = kwargs.pop('usage', None)
    if usage is None:
        usage = "%s [options]" % os.path.basename(sys.argv[0])

    parser = argparse.ArgumentParser(usage=usage, **kwargs)

    return parser



def copy_dict(in_dict, def_dict):
    """Copy a set of key-value pairs to an new dict

    Parameters
    ----------
    in_dict : `dict`
        The dictionary with the input values
    def_dict : `dict`
        The dictionary with the default values

    Returns
    -------
    outdict : `dict`
        Dictionary with only the arguments we have selected
    """
    outdict = {key:in_dict.get(key, val) for key, val in def_dict.items()}
    return outdict


def pop_values(in_dict, keylist):
    """Pop a set of key-value pairs to an new dict

    Parameters
    ----------
    in_dict : `dict`
        The dictionary with the input values
    keylist : `list`
        The values to pop

    Returns
    -------
    outdict : `dict`
        Dictionary with only the arguments we have selected
    """
    outdict = {}
    for key in keylist:
        if key in in_dict:
            outdict[key] = in_dict.pop(key)
    return outdict



def copy_pex_fields(field_names, target_class, library_class):
    """Copy a set of pexConfig.Field objects to a target class

    This is a way to make sure that all config classes in this
    package are using the same pexConfig.Field object and
    share the same parameters when appropriate

    Parameters
    ----------
    field_names : `list`
        Name of parameters to copy
    target_class : `pexConfig.Config`
        Class to add parameters to
    library_class : `pexConfig.Config`
        Class to copy parameters from

    Raises
    ------
    KeyError : one of the requested fields is not in the library class

    TypeError : the library class attribute is not a `pexConfig.Field`
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

def update_dict_from_string(o_dict, key, val, subparser_dict=None):
    """Update a dictionary with sub-dictionaries

    Parameters
    ----------
    o_dict : dict
        The output

    key : `str`
        The string we are parsing

    val : `str`
        The value

    subparser_dict : `dict` or `None`
        The subparsers used to parser the command line

    """
    idx = key.find('.')
    use_key = key[0:idx]
    remain = key[idx+1:]
    if subparser_dict is not None:
        try:
            subparser = subparser_dict[use_key[1:]]
        except KeyError:
            subparser = None
    else:
        subparser = None

    if use_key not in o_dict:
        o_dict[use_key] = {}

    def_val = None
    if subparser is not None:
        def_val = subparser.get_default(remain)
    if def_val == val:
        return

    if remain.find('.') < 0:
        o_dict[use_key][remain] = val
    else:
        update_dict_from_string(o_dict[use_key], remain, val)


def parse_args_to_dict(args, parser, subparser_dict):
    """Parse the output of argparse

    Parameters
    ----------
    args : `Namespace`
        The output of argparse

    parser : `ArgumentParser`
        The parser

    subparser_dict : `dict` or `None`
        The sub-parsers

    Returns
    -------
    o_dict : dict
         The output
    """
    o_dict = {}
    for key, val in args.__dict__.items():
        if key.find('.') < 0:
            if parser.get_default(key) == val:
                continue
            o_dict[key] = val
        else:
            update_dict_from_string(o_dict, key, val, subparser_dict)
    return o_dict



class Configurable(pipeBase.Task):
    """A small interface on top of `pipeBase.Task` to make
    it easier to handle configuration from various sources.

    The safe_update(**kwargs) method should be called at the start of any function
    that allows uses to override defualt parameter values.

    The extract_config_vals() method allows uses to get some of the configuration
    values easily.
    """
    _DefaultName = "Configurable"

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        super(Configurable, self).__init__()
        self.safe_update(**kwargs)

    def safe_update(self, **kwargs):
        """Update the configuration from a set of keywords

        Returns
        -------
        remain_dict : `dict`
            The key, val pairs not in the configuration class
        """
        base_dict = self.config.toDict()
        update_dict = {}
        remain_dict = {}
        dict_set = {}
        for key, val in kwargs.items():
            if key in base_dict:
                if isinstance(val, dict):
                    dict_set[key] = True
                    getattr(self.config, key).update(**val)
                else:
                    update_dict[key] = val
            else:
                remain_dict[key] = val
        self.config.update(**update_dict)
        top_dict = self.config.toDict()
        for key in dict_set:
            getattr(self, key).config.update(**top_dict[key])
        return remain_dict


    def extract_config_vals(self, def_dict):
        """Extract a set of configuration values to a dict

        Parameters
        ----------
        def_dict : `dict`
            Dictionary with the default values

        Returns
        -------
        ret_val : `dict`
            Dictionary with the output values
        """
        return copy_dict(self.config.toDict(), def_dict)
