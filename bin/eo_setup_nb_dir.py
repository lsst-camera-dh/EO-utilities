#!/usr/bin/env python
"""Set up a directory to run notebook analysis and copy over the examples"""

import os

import shutil

import glob

import argparse

from lsst.eo_utils.base.defaults import EO_PACKAGE_BASE

from lsst.eo_utils.base.file_utils import make_links

DEFAULT_BASEDIR = '/gpfs/slac/lsst/fs1/u/echarles/DATA/analysis'

def main():
    """Hook for setup.py"""

    parser = argparse.ArgumentParser()

    parser.add_argument('--basedir', type=str, default=DEFAULT_BASEDIR)
    parser.add_argument('--outdir', type=str, default='analysis')

    args = parser.parse_args()
    make_links(args.basedir, args.outdir)

    nb_files = glob.glob(os.path.join(EO_PACKAGE_BASE, 'nb', '*.ipynb'))
    for nb_file in nb_files:
        outpath = os.path.basename(nb_file)
        shutil.copyfile(nb_file, outpath)


if __name__ == '__main__':
    main()
