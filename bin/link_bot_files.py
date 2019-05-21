#!/usr/bin/env python

"""This module is just a command line interface to dispatch jobs to the SLAC batch farm"""

import os
import sys
import argparse

from lsst.eo_utils.base.file_utils import link_eo_bot_results_runlist

SEARCHPATH = ['/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive/LCA-10134_Cryostat',
              '/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive-test/LCA-10134_Cryostat']

GLOB_FORMAT_EOTEST = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                                  'raft_results_summary_BOT', 'v0', '*', '*_eotest_results.fits')
GLOB_FORMAT_FE55 = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                                'fe55_analysis_BOT', 'v0', '*', '*_psf_results_nsig4.fits')
GLOB_FORMAT_PTC = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                               'ptc_BOT', 'v0', '*', '*_ptc.fits')
GLOB_FORMAT_MASK_RAFT = os.path.join('{path}', 'LCA-10134_Cryostat-0001', '{run}',
                                     '*', 'v0', '*', '*_{mask}.fits')

OUTFORMAT_EOTEST = os.path.join('{outdir}', 'eotest_results', '{raft}',
                                '{raft}-{run}-{slot}_eotest_results.fits')
OUTFORMAT_FE55 = os.path.join('{outdir}', 'fe55', '{raft}',
                              '{raft}-{run}-{slot}_fe55-clusters.fits')
OUTFORMAT_PTC = os.path.join('{outdir}', 'flat', '{raft}',
                             '{raft}-{run}-{slot}_ptc.fits')
OUTFORMAT_MASK = os.path.join('{outdir}', 'masks_in', '{raft}',
                              '{raft}-{run}-{slot}_{mask}.fits')


def main():
    """Hook for setup.py"""
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", default=None,
                        help="Text file with raft and run numbers")
    parser.add_argument("--run", default=None,
                        help="Run id")
    parser.add_argument("-o", "--outdir", default='analysis',
                        help="Output directory")

    args = parser.parse_args()
    sys.stdout.write("Linking eotest summary results\n")
    #link_eo_bot_results_runlist(args.__dict__, GLOB_FORMAT_EOTEST, SEARCHPATH, OUTFORMAT_EOTEST)
    sys.stdout.write("Linking Fe55 results\n")
    link_eo_bot_results_runlist(args.__dict__, GLOB_FORMAT_FE55, SEARCHPATH, OUTFORMAT_FE55)
    sys.stdout.write("Linking PTC results\n")
    link_eo_bot_results_runlist(args.__dict__, GLOB_FORMAT_PTC, SEARCHPATH, OUTFORMAT_PTC)
    sys.stdout.write("Linking mask\n")
    for mask in ['edge_rolloff_mask', 'dark_pixel_mask']:
        link_eo_bot_results_runlist(args.__dict__, GLOB_FORMAT_MASK_RAFT, SEARCHPATH, OUTFORMAT_MASK, mask=mask)

if __name__ == '__main__':
    main()
