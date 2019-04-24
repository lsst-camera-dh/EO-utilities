"""This module contains functions to:
 1) find files of a particular type in the SLAC directory tree using the data catalog,
 2) define output filenames in a standard way
"""

import os
import sys
import glob

import yaml

try:
    from get_EO_analysis_files import get_EO_analysis_files
    from exploreRun import exploreRun
except ImportError:
    print("Warning, no datacat-utilities")


from .defaults import DATACAT_TS8_MASK_TEST_TYPES, DATACAT_BOT_MASK_TEST_TYPES,\
    SLOT_FORMAT_STRING, RAFT_FORMAT_STRING, SUMMARY_FORMAT_STRING, ALL_RAFTS


MASKFILENAME_DEFAULTS = dict(outdir='analysis', raft=None, run=None, slot=None, suffix='_mask.fits')


def makedir_safe(filepath):
    """Make a directory needed to write a file

    @param filepath (str)    The file we are going to write
    """
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass


def get_hardware_type_and_id(run):
    """Return the hardware type and hardware id for a given run

    @param run(str)   The number number we are reading

    @returns (tuple)
      htype (str) The hardware type, either
                        'LCA-10134' (aka full camera) or
                        'LCA-11021' (single raft)
      hid (str) The hardware id, e.g., RMT-004-Dev
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


def get_slot_file_basename(caller, **kwargs):
    """Return the filename for an output file from a slot-level analysis

    The format is {outdir}/{fileType}/{raft}/{testType}/{raft}-{run}-{slot}{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs           Passed to the SLOT_FORMAT_STRING.format statement

    @returns (str) The path for the file.
    """
    try:
        return str(SLOT_FORMAT_STRING.format(**kwargs))
    except KeyError as msg:
        sys.stderr.write("get_slot_file_basename failed for %s." % caller)
        raise KeyError(msg)


def get_raft_file_basename(caller, **kwargs):
    """Return the filename for an output file from a raft-level analysis

    The format is {outdir}/{fileType}/{raft}/{testType}/{raft}-{run}{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs       Passed to the RAFT_FORMAT_STRING.format statement

    @returns (str) The path for the file.
    """
    try:
        return str(RAFT_FORMAT_STRING.format(**kwargs))
    except KeyError as msg:
        sys.stderr.write("get_raft_file_basename failed for %s." % caller)
        raise KeyError(msg)


def get_summary_file_basename(caller, **kwargs):
    """Return the filename for a raft-level file

    The format is {outdir}/{fileType}/summary/{testType}/{dataset}{suffix}

    @param caller ('Task')  Object calling this function
    @param kwargs:     These are passed to the string format statement

    @returns (str) The path for the file.
    """
    try:
        return str(SUMMARY_FORMAT_STRING.format(**kwargs))
    except KeyError as msg:
        sys.stderr.write("get_summary_file_basename failed for %s." % caller)
        raise KeyError(msg)


def mask_filename(caller, outdir, raft, run, slot, **kwargs):
    """Return the filename for a mask file

    @param caller ('Task')  Object calling this function

    The following parameters are passed to the SLOT_FORMAT_STRING.format stateme
    @param outdir (str)
    @param raft (str)
    @param run (str)
    @param slot (str)
    @param kwargs:
        suffix (str)

    @returns (str) The path for the file.
    """
    return get_slot_file_basename(caller,
                                  outdir=outdir, fileType='masks',
                                  raft=raft, testType='', run=run,
                                  slot=slot, suffix=kwargs.get('suffix', '_mask.fits'))



def get_files_for_run(run_id, **kwargs):
    """Get a set of data files of a particular type for a particular run

    @param run_id (str)      The number number we are reading
    @param kwargs:
       testTypes (list)          The types of acquistions we want to include
       imageType (str)           The image type we want
       outkey (str)              Where to put the output file
       matchstr (str)            If set, only inlcude files with this string
       nfiles (int)              Number of files to include per test

    @returns (dict) Dictionary mapping slot to file names
    """
    testtypes = kwargs.get('testtypes')
    imagetype = kwargs.get('imagetype')
    outkey = kwargs.get('outkey', imagetype)
    matchstr = kwargs.get('matchstr', None)
    nfiles = kwargs.get('nfiles', None)

    outdict = {}

    if run_id.find('D') >= 0:
        db_ = 'Dev'
    else:
        db_ = 'Prod'
    handler = get_EO_analysis_files(db=db_)
    hinfo = get_hardware_type_and_id(run_id)

    for test_type in testtypes:
        r_dict = handler.get_files(testName=test_type, run=run_id,
                                   imgtype=imagetype, matchstr=matchstr)
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

    @param run_id (str)      The number number we are reading
    @param kwargs:
       mask_types (list)         The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    mask_types = kwargs.get('mask_types', None)
    hinfo = get_hardware_type_and_id(run_id)
    if mask_types is None:
        if hinfo[0] == 'LCA-11021':
            mask_types = DATACAT_TS8_MASK_TEST_TYPES
        else:
            mask_types = DATACAT_BOT_MASK_TEST_TYPES

    return get_files_for_run(run_id,
                             testtypes=mask_types,
                             outkey='MASK',
                             matchstr='_mask')


def get_mask_files(caller, **kwargs):
    """Get the name of the merged mask file

    @param kwargs   These are passed to mask_filename execpt for:
       mask (bool)  Flag to actually get the mask files

    @return (list) List of files containing only the one mask file name
    """
    if kwargs.get('mask', False):
        kwcopy = kwargs.copy()
        kwcopy['suffix'] = '_mask.fits'
        mask_files = [mask_filename(caller, **kwcopy)]
    else:
        mask_files = []
    return mask_files


def read_runlist(filepath):
    """Read a list of runs from a txt file

    @param filepath (str)    The input file with the list of runs.
                             Each line should contain raft and run number, e.g.,
                             RTM-004-Dev 6106D

    @returns (list)          A list of tuples with (raft, run)
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

    @param run(str)   The number number we are reading

    @returns (list) of raft names
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
    """Get the mapping from raft and slot to CCD in

    @param yamlfile(str)   File with the mapping

    @returns (dict) the mapping
    """
    return yaml.safe_load(open(yamlfile))


def find_eo_results(glob_format, paths, **kwargs):
    """Get a particular EO test result

    @param glob_format (str)   Formatting string for search path
    @param paths (list)        Search paths
    @param kwargs              Passed to formatting string

    @returns (dict) the mapping
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

    @param ccd_map (dcit)      Mapping between rafts, slot and CCD id
    @param fdict (dict)        Mapping between CCD id and filename
    @param outformat (str)     Formatting string for output path
    @param kwargs              Passed to formatting string

    @returns (dict) the mapping
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


def link_eo_results_runlist(args, glob_format, paths, outformat):
    """Link eo results to the analysis area

    @param args (dict)      Mapping between rafts, slot and CCD id
    @param glob_format (str)   Formatting string for search path
    @param paths (list)        Search paths
    @param outformat (str)     Formatting string for output path
    """
    run_list = read_runlist(args['input'])
    ccd_map = read_raft_ccd_map(args['mapping'])

    for run in run_list:

        run_num = run[1]
        hid = run[0].replace('-Dev', '')

        fdict = find_eo_results(glob_format, paths, run=run_num, raft=hid)
        if fdict is None:
            sys.stderr.write("Could not find eotest_results for %s %s\n" % (run_num, hid))
            continue

        link_eo_results(ccd_map, fdict, outformat, run=run_num, raft=hid, outdir=args['outdir'])
