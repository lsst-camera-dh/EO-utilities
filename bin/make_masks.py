#!/usr/bin/env python

"""This module is just a command line interface to make mask files"""

from lsst.eo_utils.base.mask_analysis import MaskAddTask


def main():
    """Hook for setup.py"""
    MaskAddTask.parseAndRun()

if __name__ == '__main__':
    main()
