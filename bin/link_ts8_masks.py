#!/usr/bin/env python

"""This module is just a command line interface to dispatch jobs to the SLAC batch farm"""

import os
import argparse

from lsst.eo_utils.base.file_utils import link_eo_results_runlist

SEARCHPATH = ['/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive/LCA-11021_RTM',
              '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM',
              '/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive/LCA-11021_RTM',
              '/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive-test/LCA-11021_RTM']


GLOB_FORMAT_RAFT = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                '*', 'v0', '*', '*_{mask}.fits')
GLOB_FORMAT_SLOT = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                                '*', 'v0', '*', '*', '*_{mask}.fits')
OUTFORMAT = os.path.join('{outdir}', 'eotest_results', '{raft}', '{raft}-{run}-{slot}_{mask}.fits')



def main():
    """Hook for setup.py"""
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", default=None,
                        help="Text file with raft and run numbers")
    parser.add_argument("-o", "--outdir", default='analysis',
                        help="Output directory")
    parser.add_argument("-m", "--mapping", default=None,
                        help="Yaml file with raft to ccd mapping")

    args = parser.parse_args()

    for mask in ['rolloff_defects_mask', 'dark_pixel_mask']:
        link_eo_results_runlist(args.__dict__, GLOB_FORMAT_RAFT, SEARCHPATH, OUTFORMAT, mask=mask)

    for mask in ['bright_pixel_mask', 'traps_mask']:
        link_eo_results_runlist(args.__dict__, GLOB_FORMAT_SLOT, SEARCHPATH, OUTFORMAT, mask=mask)

if __name__ == '__main__':
    main()
