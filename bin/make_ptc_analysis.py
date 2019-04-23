#!/usr/bin/env python

"""This module is just a command line to get summary gain data from ptc analyses"""

from lsst.eo_utils.flat.ptc import ptc_analysis

def main():
    """Hook for setup.py"""
    ptc_analysis.run()

if __name__ == '__main__':
    main()
