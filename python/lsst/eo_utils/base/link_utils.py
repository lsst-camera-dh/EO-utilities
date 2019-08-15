"""Functions to help linking to files at IR2"""

import os
import sys

from .file_utils import link_eo_results_runlist, link_eo_calib_runlist,\
    link_eo_bot_results_runlist

SEARCHPATH_TS8 = ['/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive/LCA-11021_RTM',
                  '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM',
                  '/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive/LCA-11021_RTM',
                  '/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive-test/LCA-11021_RTM']

SEARCHPATH_BOT = ['/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive/LCA-10134_Cryostat',
                  '/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive-test/LCA-10134_Cryostat']


GLOB_FORMAT_EOTEST_TS8 = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                      'collect_raft_results', 'v0', '*', '*_eotest_results.fits')
GLOB_FORMAT_FE55_TS8 = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                    'fe55_raft_analysis', 'v0', '*', '*_psf_results_nsig4.fits')
GLOB_FORMAT_PTC_TS8 = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                   'ptc_raft', 'v0', '*', 'S*', '*_ptc.fits')
GLOB_FORMAT_PD_CALIB_TS8 = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                        'qe_raft_analysis', 'v0', '*', 'ts8_pd_calibration_*.dat')

GLOB_FORMAT_MASK_RAFT_TS8 = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                         '*', 'v0', '*', '*_{mask}.fits')
GLOB_FORMAT_MASK_SLOT_TS8 = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                         '*', 'v0', '*', '*', '*_{mask}.fits')

GLOB_FORMAT_EOTEST_BOT = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                                      'raft_results_summary_BOT', 'v0',
                                      '*', '*_eotest_results.fits')
GLOB_FORMAT_FE55_BOT = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                                    'fe55_analysis_BOT', 'v0',
                                    '*', '*_psf_results_nsig4.fits')
GLOB_FORMAT_PTC_BOT = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                                   'ptc_BOT', 'v0', '*', '*_ptc.fits')
GLOB_FORMAT_MASK_RAFT_BOT = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                                         '*', 'v0', '*', '*_{mask}.fits')

OUTFORMAT_EOTEST = os.path.join('{outdir}', '{teststand}', 'eotest_results',
                                '{raft}', '{raft}-{run}-{slot}_eotest_results.fits')
OUTFORMAT_FE55 = os.path.join('{outdir}', '{teststand}', 'tables', '{raft}',
                              'fe55', '{raft}-{run}-{slot}_b-orig_s-orig_fe55_clusters.fits')

OUTFORMAT_PD_CALIB = os.path.join('{outdir}', '{teststand}', 'pd_calib',
                                  '{raft}', '{raft}-{run}-pd_calib.dat')
OUTFORMAT_PTC = os.path.join('{outdir}', '{teststand}', 'flat', '{raft}',
                             '{raft}-{run}-{slot}_b-orig_s-orig_ptc.fits')
OUTFORMAT_MASK = os.path.join('{outdir}', '{teststand}', 'masks_in', '{raft}',
                              '{raft}-{run}-{slot}_{mask}.fits')


def link_ts8_files(args):
    """Link eo results to the analysis area

    Parameters
    ----------
    args : `dict`
        Mapping between rafts, slot and CCD id
    """
    sys.stdout.write("Linking eotest summary results\n")
    link_eo_results_runlist(args, GLOB_FORMAT_EOTEST_TS8, SEARCHPATH_TS8, OUTFORMAT_EOTEST)
    sys.stdout.write("Linking Fe55 results\n")
    link_eo_results_runlist(args, GLOB_FORMAT_FE55_TS8, SEARCHPATH_TS8, OUTFORMAT_FE55)
    sys.stdout.write("Linking PTC results\n")
    link_eo_results_runlist(args, GLOB_FORMAT_PTC_TS8, SEARCHPATH_TS8, OUTFORMAT_PTC)
    sys.stdout.write("Linking Photo-diode calibrations\n")
    link_eo_calib_runlist(args, GLOB_FORMAT_PD_CALIB_TS8, SEARCHPATH_TS8, OUTFORMAT_PD_CALIB)

    sys.stdout.write("Linking mask\n")
    for mask in ['rolloff_defects_mask', 'dark_pixel_mask']:
        link_eo_results_runlist(args, GLOB_FORMAT_MASK_RAFT_TS8,
                                SEARCHPATH_TS8, OUTFORMAT_MASK, mask=mask)

    for mask in ['bright_pixel_mask', 'traps_mask']:
        link_eo_results_runlist(args, GLOB_FORMAT_MASK_SLOT_TS8,
                                SEARCHPATH_TS8, OUTFORMAT_MASK, mask=mask)

def link_bot_files(args):
    """Link eo results to the analysis area

    Parameters
    ----------
    args : `dict`
        Mapping between rafts, slot and CCD id
    """
    sys.stdout.write("Linking eotest summary results\n")
    #link_eo_bot_results_runlist(args, GLOB_FORMAT_EOTEST_BOT, SEARCHPATH_BOT, OUTFORMAT_EOTEST)
    sys.stdout.write("Linking Fe55 results\n")
    link_eo_bot_results_runlist(args, GLOB_FORMAT_FE55_BOT, SEARCHPATH_BOT, OUTFORMAT_FE55)
    sys.stdout.write("Linking PTC results\n")
    link_eo_bot_results_runlist(args, GLOB_FORMAT_PTC_BOT, SEARCHPATH_BOT, OUTFORMAT_PTC)
    sys.stdout.write("Linking mask\n")
    for mask in ['edge_rolloff_mask', 'dark_pixel_mask']:
        link_eo_bot_results_runlist(args, GLOB_FORMAT_MASK_RAFT_BOT,
                                    SEARCHPATH_BOT, OUTFORMAT_MASK, mask=mask)
