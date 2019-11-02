#!/usr/bin/env python

"""This module is just a command line interface to dispatch jobs to the SLAC batch farm"""

import argparse

from lsst.eo_utils.base.link_utils import link_run


def main():
    """Hook for setup.py"""
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', "--input", default=None, required=True,
                        help="Run id for input run")
    parser.add_argument('-o', "--output", default=None, required=True,
                        help="Run id for output run")
    parser.add_argument('-g', "--glob_format", default=None, required=True,
                        help='String to match to link files')

    args = parser.parse_args()
    link_run(args.__dict__)

if __name__ == '__main__':
    main()
