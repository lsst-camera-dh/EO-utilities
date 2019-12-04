#!/usr/bin/env python

"""This module just builds a markdown table describing all the tasks"""

import os

import sys

import argparse

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils import base, bias, flat, fe55, sflat, dark, qe, ppump, meta

MODULE_LIST = [base, bias, flat, fe55, sflat, dark, qe, ppump, meta]

def main():
    """Hook for setup.py"""
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', "--output", type=str, default=None,
                        help="Output file")

    args = parser.parse_args()
    if args.output is None:
        outfile = sys.stdout
    else:
        outfile = open(args.output, 'w')

    EO_TASK_FACTORY.make_plot_names_txt(outfile)


if __name__ == '__main__':
    main()
