#!/usr/bin/env python
"""Set up a directory to run EO analysis and link to a base output area"""

import argparse

from lsst.eo_utils.base.file_utils import make_links

DEFAULT_BASEDIR = '/gpfs/slac/lsst/fs1/u/echarles/DATA/analysis'

def main():
    """Hook for setup.py"""

    parser = argparse.ArgumentParser()

    parser.add_argument('--basedir', type=str, default=DEFAULT_BASEDIR)
    parser.add_argument('--outdir', type=str, default='analysis')

    args = parser.parse_args()
    make_links(args.basedir, args.outdir)

if __name__ == '__main__':
    main()
