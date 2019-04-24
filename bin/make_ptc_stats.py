#!/usr/bin/env python

"""This module is just a command line to get summary gain data from ptc analyses"""

from lsst.eo_utils.flat.ptc import ptc_stats

def main():
    """Hook for setup.py"""
    ptc_stats.parseAndRun()

if __name__ == '__main__':
    main()
