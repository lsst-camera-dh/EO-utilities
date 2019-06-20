#!/usr/bin/env python

"""This module is just a command line interface to dispatch jobs to the SLAC batch farm"""

import argparse

from lsst.eo_utils.base.link_utils import link_bot_files


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
    link_bot_files(args.__dict__)

if __name__ == '__main__':
    main()
