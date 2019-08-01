#!/usr/bin/env python

"""This module is just a command line interface to dispatch jobs to the SLAC batch farm"""

import argparse

from lsst.eo_utils.base.link_utils import link_ts8_files


def main():
    """Hook for setup.py"""
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", default=None,
                        help="Text file with raft and run numbers")
    parser.add_argument("--run", default=None,
                        help="Run id")
    parser.add_argument("--raft", default=None,
                        help="Raft id")
    parser.add_argument("-o", "--outdir", default='analysis',
                        help="Output directory")
    parser.add_argument("--teststand", default='ts8',
                        help='Teststand')
    parser.add_argument("-m", "--mapping", default=None,
                        help="Yaml file with raft to ccd mapping")

    args = parser.parse_args()
    link_ts8_files(args.__dict__)


if __name__ == '__main__':
    main()
