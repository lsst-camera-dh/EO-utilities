#!/usr/bin/env python
"""Specialize template code for a particular task"""

import os

import glob

import argparse

from lsst.eo_utils.base.file_utils import makedir_safe

DEFAULT_BASEDIR = '/gpfs/slac/lsst/fs1/u/echarles/DATA/analysis'

def make_links(basedir, outdir):
    """Make links for an analysis directory

    Parameters
    ----------
    basedir : `str`
        Area we are pointing to
    outdir : `str`
        Area we are writing to
    """
    print("Linking directories in %s to %s" % (basedir, outdir))

    topdirs = glob.glob(os.path.join(basedir, '*'))
    for topdir in topdirs:
        if os.path.basename(topdir) in ['test']:
            continue
        dir_glob = glob.glob(os.path.join(topdir, '*'))
        for link_from in dir_glob:
            if os.path.basename(link_from) in ['plots', 'tables']:
                continue
            link_to = link_from.replace(basedir, outdir)
            comm = 'ln -s %s %s' % (link_from, link_to)
            makedir_safe(link_to)
            os.system(comm)


def main():
    """Hook for setup.py"""

    parser = argparse.ArgumentParser()

    parser.add_argument('--basedir', type=str, default=DEFAULT_BASEDIR)
    parser.add_argument('--outdir', type=str, default='analysis')

    args = parser.parse_args()
    make_links(args.basedir, args.outdir)


if __name__ == '__main__':
    main()
