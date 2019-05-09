"""This module contains functions to:
 1) find files of a particular type in the SLAC directory tree using the data catalog,
 2) define output filenames in a standard way
"""

import os
import sys
import glob

from collections import OrderedDict

import yaml

try:
    from get_EO_analysis_files import get_EO_analysis_files
    from exploreRun import exploreRun
except ImportError:
    print("Warning, no datacat-utilities")


from .defaults import ALL_RAFTS, ALL_SLOTS, ARCHIVE_SLAC


# These are the standard input filenames
TS8_GLOB_STRING =\
    '{archive}/LCA-11021_RTM/LCA-11021_{raft}*/{run}/{testName}/v0/*/{slot}/*{imgtype}*.fits'
BOT_GLOB_STRING =\
    '{archive}/LCA-10134_Cryostat/LCA-10134_Cryostat-0001/{run}/' +\
    'BOT_acq/v0/*/{testName}*{imgtype}*/MC_C*{raft}_{slot}.fits'


# These strings define the standard output filenames
SLOT_FORMAT_STRING = '{outdir}/{fileType}/{raft}/{testType}/{raft}-{run}-{slot}{suffix}'
RAFT_FORMAT_STRING = '{outdir}/{fileType}/{raft}/{testType}/{raft}-{run}-RFT{suffix}'
SUMMARY_FORMAT_STRING = '{outdir}/{fileType}/summary/{testType}/{dataset}{suffix}'
SUPERBIAS_FORMAT_STRING =\
    '{outdir}/superbias/{raft}/{raft}-{run}-{slot}_superbias_b-{bias}{suffix}'
SUPERBIAS_STAT_FORMAT_STRING =\
    '{outdir}/superbias/{raft}/{raft}-{run}-{slot}_{stat}_b-{bias}{suffix}'




def makedir_safe(filepath):
    """Make a directory needed to write a file

    Parameters
    ----------
    filepath : `str`
        The file we are going to write
    """
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass


def get_hardware_type_and_id(run):
    """Return the hardware type and hardware id for a given run

    Parameters
    ----------
    run : `str`
        The number number we are reading

    Returns
    -------
    htype : `str`
        The hardware type, either 'LCA-10134' (aka full camera) or 'LCA-11021' (single raft)
    hid : `str`
        The hardware id, e.g., RMT-004-Dev
    """
    if run.find('D') >= 0:
        db_ = 'Dev'
    else:
        db_ = 'Prod'
    ex_run = exploreRun(db=db_)
    hsn = ex_run.hardware_sn(run=run)
    tokens = hsn.split('_')
    htype = tokens[0]
    hid = tokens[1].replace('-Dev', '')
    return (htype, hid)



class FilenameFormat:
    """Small class to define the format of a particular file

    New `FilenameFormat` objects should be created at the
    module level using the
    FILENAME_FORMATS.add_format() function as that will
    ensure that they are stored in the mapping of formats,
    making it easier to find a file of a particular type, e.g.:

    from lsst.eo_utils.base.file_utils import FILENAME_FORMATS

    FMT_FORMAT = FILENAME_FORMATS.add_format("fmt", "{prefix}_name_{suffix}", suffix="")
    """

    def __init__(self, fmt, **kwargs):
        """C'tor

        Parameters
        ----------
        fmt : `str`
            String that defines the file format
        kwargs
            Used to set default values
        """
        self._format = fmt
        self._keys = FilenameFormat._get_format_keys(self._format)
        self._defaults = kwargs.copy()
        self._missing = []
        for key in self._keys:
            if key not in self._defaults:
                self._missing.append(key)

    def key_dict(self):
        """Returns `dict` with all the keys and default values"""
        ret_dict = {key:self._defaults.get(key, None) for key in self._keys}
        return ret_dict

    def check(self, **kwargs):
        """Checks which required keys are still missing

        Parameters
        ----------
        kwargs
            Format key : value pairs

        Returns
        -------
        missed : `list`
            List of formatting keys that are missing
        """
        missed = []
        for miss in self._missing:
            if miss not in kwargs and miss not in missed:
                missed.append(miss)
        return missed

    def __call__(self, caller=None, **kwargs):
        """C'tor

        Parameters
        ----------
        caller : `object` or `None`
            Object calling this function
        kwargs
            Key : value pairs used to format string

        Returns
        -------
        retval: `str`
            Formatted filename

        Raises
        ------
        KeyError : If not all required formatting keys are present
        """
        use_vals = self._defaults.copy()
        use_vals.update(kwargs)
        try:
            return self._format.format(**use_vals)
        except KeyError:
            missed = self.check(**kwargs)
            raise KeyError("FilenameFormat missing parameters for %s : %s" % (caller, missed))


    @staticmethod
    def _findall(string, sep):
        """Find all the values of sep in string

        Returns
        -------
        outlist : `list`
            List of the positions where the seperator occurs
        """
        outlist = []
        for idx, char in enumerate(string):
            if char == sep:
                outlist.append(idx)
        return outlist

    @staticmethod
    def _get_format_keys(string):
        """Get the set of keys requird to format this file

        Returns
        -------
        outlist : `list`
            List of the required formatting keys
        """
        left_vals = FilenameFormat._findall(string, '{')
        right_vals = FilenameFormat._findall(string, '}')
        outlist = []
        for left, right in zip(left_vals, right_vals):
            field = string[left+1:right]
            if field not in outlist:
                outlist.append(field)
        return outlist



class FilenameFormatDict:
    """Small class to keep track of filename formats"""

    def __init__(self):
        """C'tor"""
        self._formats = OrderedDict()

    def keys(self):
        """Returns the `list` of types of file names"""
        return self._formats.keys()

    def values(self):
        """Returns the `list` of `FilenameFormat` objects"""
        return self._formats.values()

    def items(self):
        """Returns `list` of name `FilenameFormat` keys"""
        return self._formats.items()

    def __getitem__(self, key):
        """Returns a single `FilenameFormat` object by name"""
        return self._formats[key]

    def __call__(self, key, **kwargs):
        """Get the formatted filename

        Parameters
        ----------
        key : `str`
            The key that identifies a `FilenameFormat`
        kwargs
            Passed to the `FilenameFormat` object

        Returns
        -------
        retval : `str`
            The corresponding filename
        """
        return self._formats[key](**kwargs)

    def add_format(self, key, fmt, **kwargs):
        """Add an item to the dict

        Parameters
        ----------
        key : `str`
            The key to add the item under
        fmt : `str`
            String that defines the file format
        kwargs
            Used to set default values

        Returns
        -------
        new_format : `FilenameFormat`
            The newly created object
        """
        if key in self._formats:
            raise KeyError("Key %s is already in FilenameFormatDict" % key)
        new_format = FilenameFormat(fmt, **kwargs)
        self._formats[key] = new_format
        return new_format


FILENAME_FORMATS = FilenameFormatDict()

SLOT_BASE_FORMATTER = FILENAME_FORMATS.add_format('slot_basename', SLOT_FORMAT_STRING)
RAFT_BASE_FORMATTER = FILENAME_FORMATS.add_format('raft_basename', RAFT_FORMAT_STRING)
SUM_BASE_FORMATTER = FILENAME_FORMATS.add_format('summary_basename', SUMMARY_FORMAT_STRING)
TS8_MASKIN_FORMATTER = FILENAME_FORMATS.add_format('ts8_mask_in', SLOT_FORMAT_STRING,
                                                   fileType='masks_in', testType='', suffix='_mask.fits')
MASK_FORMATTER = FILENAME_FORMATS.add_format('mask', SLOT_FORMAT_STRING,
                                             fileType='masks', testType='',
                                             suffix='_mask.fits')
SUPERBIAS_FORMATTER = FILENAME_FORMATS.add_format('superbias',
                                                  SUPERBIAS_FORMAT_STRING,
                                                  superbias=None, suffix='')
SUPERBIAS_STAT_FORMATTER = FILENAME_FORMATS.add_format('superbias_stat',
                                                       SUPERBIAS_STAT_FORMAT_STRING,
                                                       bias=None, suffix='')
TS8_FORMATTER = FILENAME_FORMATS.add_format('ts8_images',
                                            TS8_GLOB_STRING,
                                            archive=ARCHIVE_SLAC)
BOT_FORMATTER = FILENAME_FORMATS.add_format('bot_images',
                                            BOT_GLOB_STRING,
                                            archive=ARCHIVE_SLAC)

def get_ts8_files_glob(**kwargs):
    """Returns a `list` with the matching file names using the format string for TS8 data """
    outdict = {}
    for slot in ALL_SLOTS:
        glob_string = TS8_FORMATTER(slot=slot, **kwargs)
        outdict[slot] = sorted(glob.glob(glob_string))
    return outdict



def get_bot_files_glob(**kwargs):
    """Returns a `list` with the matching file names using the format string for BOT data """
    outdict = {}
    for raft in ALL_RAFTS:
        raftdict = {}
        for slot in ALL_SLOTS:
            glob_string = BOT_FORMATTER(raft=raft, slot=slot, **kwargs)
            raftdict[slot] = sorted(glob.glob(glob_string))
        outdict[raft] = raftdict
    return outdict

def merge_file_dicts(dict_1, dict_2):
    """Combine a pair of file dictionaries

    Parameters
    ----------
    dict_1 : `dict`
        A dictionary of data_ids or filenames keyed by raft, slot, filetype
    dict_2 : `dict`
        A dictionary of data_ids or filenames keyed by raft, slot, filetype

    Returns
    -------
    out_dict : `dict`
        A dictionary of data_ids or filenames keyed by raft, slot, filetype
    """
    out_dict = dict_1.copy()
    for key, val in dict_2.items():
        if isinstance(val, dict):
            out_dict[key] = merge_file_dicts(out_dict[key], val)
        else:
            out_dict[key] = val
    return out_dict


def get_files_for_run(run_id, **kwargs):
    """Get a set of data files of a particular type for a particular run

    Parameters
    ----------
    run_id : `str`
        The number number we are reading

    Keywords
    --------
    testTypes : `list`
        The types of acquistions we want to include
    imageType : `str`
        The image type we want
    outkey : `str`
        Where to put the output file
    matchstr : `str`
        If set, only inlcude files with this string
    nfiles : `int`
        Number of files to include per test

    Returns
    -------
    outdict : `dict`
        Dictionary mapping slot to file names
    """
    testtypes = kwargs.get('testtypes')
    imagetype = kwargs.get('imagetype')
    outkey = kwargs.get('outkey', imagetype)
    matchstr = kwargs.get('matchstr', None)
    nfiles = kwargs.get('nfiles', None)

    outdict = {}

    hinfo = get_hardware_type_and_id(run_id)

    if kwargs.get('datacat', False):
        if run_id.find('D') >= 0:
            db_ = 'Dev'
        else:
            db_ = 'Prod'
        handler = get_EO_analysis_files(db=db_)
    else:
        handler = None

    for test_type in testtypes:
        if handler is not None:
            r_dict = handler.get_files(testName=test_type, run=run_id,
                                       imgtype=imagetype, matchstr=matchstr)
        else:
            if imagetype is None:
                imgtype = None
            else:
                imgtype = imagetype.lower()
            if hinfo[0] == 'LCA-11021':
                r_dict = get_ts8_files_glob(run=run_id,
                                            testName=test_type,
                                            imgtype=imgtype,
                                            raft=hinfo[1])
            else:
                r_dict = get_bot_files_glob(run=run_id,
                                            testName=test_type,
                                            imgtype=imgtype)
        for key, val in r_dict.items():
            if hinfo[0] == 'LCA-11021':
                # Raft level data
                if nfiles is None:
                    filelist = val
                else:
                    filelist = val[0:min(nfiles, len(val))]
                if key in outdict:
                    outdict[key][outkey] += filelist
                else:
                    outdict[key] = {outkey:filelist}
            else:
                # BOT level data, need to add extra layer
                if key not in outdict:
                    outdict[key] = {}
                for key2, val2 in val.items():
                    if nfiles is None:
                        filelist = val2
                    else:
                        filelist = val2[0:min(nfiles, len(val2))]
                    if key2 in outdict[key]:
                        outdict[key][key2][outkey] += filelist
                    else:
                        outdict[key][key2] = {outkey:filelist}

    if hinfo[0] == 'LCA-11021':
        return {hinfo[1]:outdict}

    return outdict


def get_mask_files_run(run_id, **kwargs):
    """Get a set of mask for a particular run

    Parameters
    ----------
    run_id : `str`
        The number number we are reading

    Keywords
    --------
    mask_types : `list`
        The types of acquistions we want to include


    Returns
    -------
    retval : `dict`
        Dictionary mapping slot to file names
    """
    hinfo = get_hardware_type_and_id(run_id)

    kwcopy = kwargs.copy()
    outdict = {}
    rafts = kwcopy.pop('rafts')
    if rafts is None:
        raft = kwcopy.get('raft', None)
        if raft is None:
            rafts = [hinfo[1]]
        else:
            rafts = [raft]

    for raft in rafts:
        kwcopy['raft'] = raft
        slotdict = {}
        outdict[raft] = slotdict
        for slot in ALL_SLOTS:
            glob_string = TS8_MASKIN_FORMATTER(slot=slot, run=run_id,
                                               suffix='*_mask.fits', **kwcopy)
            slotdict[slot] = dict(MASK=sorted(glob.glob(glob_string)))

    return outdict


def read_runlist(filepath):
    """Read a list of runs from a txt file

    Parameters
    ----------
    filepath : `str`
        The input file with the list of runs.
        Each line should contain raft and run number, e.g., RTM-004-Dev 6106D

    Returns
    -------
    outlist : `list`
        A list of tuples with (raft, run)
    """
    fin = open(filepath)
    lin = fin.readline()

    outlist = []
    while lin:
        tokens = lin.split()
        if len(tokens) == 2:
            outlist.append(tokens)
        lin = fin.readline()
    return outlist


def get_raft_names_dc(run):
    """Get the list of rafts used for a particular run

    Parameters
    ----------
    run : `str`
        The number number we are reading

    Returns
    -------
    retval : `list`
        The list of raft names

    Raises
    ------
    ValueError : If the hardware type is not recognized
    """
    hinfo = get_hardware_type_and_id(run)

    htype = hinfo[0]
    hid = hinfo[1]
    if htype == 'LCA-11021':
        return [hid]
    if htype == 'LCA-10134':
        return ALL_RAFTS
    raise ValueError("Unrecognized hardware type %s" % htype)


def read_raft_ccd_map(yamlfile):
    """Get the mapping from raft and slot to CCD

    Parameters
    ----------
    yamlfile : `str`
        File with the mapping

    Returns
    -------
    retval : `dict`
        The mapping key raft, slot to CCD serial number
    """
    return yaml.safe_load(open(yamlfile))


def find_eo_results(glob_format, paths, **kwargs):
    """Get a particular EO test result

    Parameters
    ----------
    glob_format : `str`
        Formatting string for search path
    paths : `list`
        Search paths
    kwargs
        Passed to formatting string

    Returns
    -------
    odict : `dict`
        The mapping of run, raft to filename
    """
    for path in paths:
        globstring = glob_format.format(path=path, **kwargs)
        globfiles = glob.glob(globstring)
        if len(globfiles) != 9:
            continue
        odict = {}
        for fname in globfiles:
            sensor = os.path.basename(fname).split('_')[0].replace('-Dev', '')
            odict[sensor] = fname
        return odict
    return None


def link_eo_results(ccd_map, fdict, outformat, **kwargs):
    """Link eo results to the analysis area

    Parameters
    ----------
    ccd_map : `dict`
        Mapping between rafts, slot and CCD id
    fdict : `dict`
        Mapping between CCD id and filename
    outformat : `str`
        Formatting string for output path
    kwargs
        Passed to formatting string

    Raises
    ------
    KeyError : If missing values in fdict
    """
    raft = kwargs.pop('raft')
    slot_map = ccd_map[raft]
    for slot, val in slot_map.items():
        try:
            fname = fdict[val]
        except KeyError as msg:
            print(fdict.keys())
            raise KeyError(msg)
        outpath = outformat.format(raft=raft, slot=slot, **kwargs)
        makedir_safe(outpath)
        os.system("ln -s %s %s" % (fname, outpath))


def link_eo_results_runlist(args, glob_format, paths, outformat, **kwargs):
    """Link eo results to the analysis area

    Parameters
    ----------
    args : `dict`
        Mapping between rafts, slot and CCD id
    glob_format : `str`
        Formatting string for search path
    paths : `list`
        Search paths for input datra
    outformat : `str`
        Formatting string for output path
    """
    run_list = read_runlist(args['input'])
    ccd_map = read_raft_ccd_map(args['mapping'])

    for run in run_list:

        run_num = run[1]
        hid = run[0].replace('-Dev', '')

        fdict = find_eo_results(glob_format, paths, run=run_num, raft=hid, **kwargs)
        if fdict is None:
            sys.stderr.write("Could not find eotest_results for %s %s\n" % (run_num, hid))
            continue

        link_eo_results(ccd_map, fdict, outformat, run=run_num,
                        raft=hid, outdir=args['outdir'], **kwargs)
