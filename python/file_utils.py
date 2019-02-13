"""Functions to find files of a particular type in the SLAC directory tree"""

import os
import glob

from get_EO_analysis_files import get_EO_analysis_files

ACQ_TYPES_DEFAULT = ['fe55_raft_acq',
                     'flat_pair_raft_acq',
                     'sflat_raft_acq',
                     'qe_raft_acq',
                     'dark_raft_acq']

MASK_TYPES_DEFAULT = ['fe55_raft_analysis',
                      'dark_defects_raft',
                      'traps_raft',
                      'bright_defects_raft']

RD_ROOT_FOLDER = '/gpfs/slac/lsst/fs1/g/data/R_and_D/'
RAFT_ROOT_FOLDER = '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM/'
DEFAULT_DB = 'Dev'


def superbias_filename(outdir, raft, run_num, slot, bias_type):    
    """Return the filename for a superbias file

    Parameters
    ----------
    outdir:               str
    raft:                 str
    run_num:              str
    slot:                 str
    bias_type:            str

    Returns
    -------
    outpath:              str
    """
    outpath = os.path.join(outdir,
                           '%s-%s-%s_superbias_b-%s.fits' % (raft, run_num, slot, bias_type))
    return outpath


def superbias_stat_filename(outdir, raft, run_num, slot, tat_type, superbias_type):    
    """Return the filename for a superbias file

    Parameters
    ----------
    outdir:               str
    raft:                 str
    run_num:              str
    slot:                 str
    stat_type:            str
    superbias_type:       str

    Returns
    -------
    outpath:              str
    """
    outpath = os.path.join(outdir,
                           '%s-%s-%s_%s_b-%s.fits' %\
                               (raft, run_num, slot, stat_type.lower(), bias_type))
    return outpath


def bias_plot_basename(outdir, raft, run_num, slot, plotname,
                       bias_type=None, superbias_type=None):    
    """Return the filename for a superbias file

    Parameters
    ----------
    outdir:               str
    raft:                 str
    run_num:              str
    slot:                 str
    bias_type:            str
    superbias_type:       str

    Returns
    -------
    outpath:              str
    """
    outpath = os.path.join(outdir, "plots", 
                           "%s-%s-%s_%s" % (raft, run_num, slot, plotname))

    if bias_type is None:
        outpath += "_b-none"
    else:
        outpath += "_b-%s" % bias_type
        
    if superbias_type is None:
        outpath += "_s-none"
    else:
        outpath += "_s-%s" % superbias_type
    
    return outpath

  
def superbias_plot_basename(outdir, raft, run_num, slot, plotname,
                            superbias_type=None):    
    """Return the filename for a superbias file

    Parameters
    ----------
    outdir:               str
    raft:                 str
    run_num:              str
    slot:                 str
    superbias_type:       str

    Returns
    -------
    outpath:              str
    """
    outpath = os.path.join(outdir, "plots", 
                           "%s-%s-%s_%s" % (raft, run_num, slot, plotname))

    if superbias_type is None:
        outpath += "_b-none"
    else:
        outpath += "_b-%s" % superbias_type
           
    return outpath


def get_bias_files_run(run_id, acq_types=None, db=DEFAULT_DB):
    """Get a set of bias files out of a folder

    Parameters
    ----------
    run_id:          str
    acd_types:       list
    db:              str

    Returns
    -------
    outdict:  dict
       Dictionary maping slot to bias file names
    """
    outdict = {}
    if acq_types is None:
        acq_types = ACQ_TYPES_DEFAULT

    handler = get_EO_analysis_files(db=db)
    for acq_type in acq_types:
        r_dict = handler.get_files(testName=acq_type, run=run_id, imgtype='BIAS')
        for key, val in r_dict.items():
            if key in outdict:
                outdict[key] += val
            else:
                outdict[key] = val
    return outdict


def get_mask_files_run(run_id, mask_types=None, db=DEFAULT_DB):
    """Get a set of bias files out of a folder

    Parameters
    ----------
    run_id:          str
    mask_types:      list
    db:              str

    Returns
    -------
    outdict:  dict
       Dictionary maping slot to bias file names
    """
    outdict = {}
    if mask_types is None:
        mask_types = MASK_TYPES_DEFAULT

    handler = get_EO_analysis_files(db=db)
    for mask_type in mask_types:
        r_dict = handler.get_files(testName=mask_type, run=run_id, imgtype='FLAT')
        for key, val in r_dict.items():
            if key in outdict:
                outdict[key] += val
            else:
                outdict[key] = val
    return outdict


def get_bias_files_rd(raft, folder, root_data_path=RD_ROOT_FOLDER):
    """Get a set of bias files out of a folder

    Parameters
    ----------
    raft:        str
    folder:          str
    root_data_path:  str

    Returns
    -------
    bias_files:  dict
       Dictionary maping slot to bias file name
    """
    files = sorted(glob.glob(os.path.join(root_data_path, raft, folder,
                                          'data', '*Bias*.fits*')))
    bias_files = dict()
    for item in files:
        slot = "S%s" % os.path.basename(item).split('_')[0]
        bias_files[slot] = item
    return bias_files


def get_bias_files_raft(raft, folder, acq_type='dark_raft_acq',
                        root_data_path=RAFT_ROOT_FOLDER):
    """Get a set of bias files out of a folder

    Parameters
    ----------
    raft:        str
    folder:          str
    root_data_path:  str

    Returns
    -------
    bias_files:  dict
       Dictionary maping slot to bias file name
    """
    files = []

    full_raft = "LCA-11021_%s"% raft
    glob_string = os.path.join(root_data_path, full_raft, folder, acq_type,
                               'v0', '*', '*', '*_bias_*.fits')
    files = sorted(glob.glob(glob_string))
    bias_files = dict()

    for item in files:
        slot = "%s" % os.path.dirname(item).split('/')[-1]
        bias_files[slot] = item
    return bias_files


def get_bias_files_slot(raft, folder, slot,
                        acq_types=None,
                        root_data_path=RAFT_ROOT_FOLDER):
    """Get a set of bias files out of a folder

    Parameters
    ----------
    raft:        str
    folder:          str
    slot:            str
    acq_types:       list
    root_data_path:  str

    Returns
    -------
    files:            list
       All the files matching the request
    """
    if acq_types is None:
        acq_types = ACQ_TYPES_DEFAULT
    files = []
    for acq_type in acq_types:
        glob_string = os.path.join(root_data_path, "LCA-11021_%s" % raft, folder,
                                   acq_type, 'v0', '*', slot, '*_bias_*.fits')
        files += sorted(glob.glob(glob_string))
    return files


def get_mask_files_slot(raft, folder, sensor_id,
                        mask_types=None,
                        root_data_path=RAFT_ROOT_FOLDER):
    """Get a set of mask files out of a folder

    Parameters
    ----------
    raft:        str
    folder:          str
    sensor_id:       str
    acq_types:       list
    root_data_path:  str

    Returns
    -------
    files:            list
       All the files matching the request
    """
    if mask_types is None:
        mask_types = MASK_TYPES_DEFAULT
    files = []
    for mask_type in mask_types:
        files += sorted(glob.glob(os.path.join(root_data_path, "LCA-11021_%s" % raft, folder,
                                               mask_type, 'v0', '*', '%s_*_mask.fits' % sensor_id)))
    return files
