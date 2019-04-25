#!/usr/bin/env python

"""This module is just a command line interface to dispatch jobs to the SLAC batch farm"""

import os
import argparse

from lsst.eo_utils.base.file_utils import link_eo_results_runlist

SEARCHPATH = ['/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive/LCA-11021_RTM',
              '/gpfs/slac/lsst/fs3/g/data/jobHarness/jh_archive-test/LCA-11021_RTM',
              '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive/LCA-11021_RTM',
              '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM']


GLOB_FORMAT = os.path.join('{path}', 'LCA-11021_{raft}*', '{run}',
                           'ptc_raft', 'v0', '*', 'S*', '*_ptc.fits')
OUTFORMAT = os.path.join('{outdir}', 'flat', '{raft}', '{raft}-{run}-{slot}_ptc.fits')



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
    link_eo_results_runlist(args.__dict__, GLOB_FORMAT, SEARCHPATH, OUTFORMAT)

if __name__ == '__main__':
    main()
