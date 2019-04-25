#!/usr/bin/env python

"""This module is just a command line to get summary gain data from ptc analyses"""

from lsst.eo_utils.flat.ptc import PTCTask

def main():
    """Hook for setup.py"""
    PTCTask.parse_and_run()

if __name__ == '__main__':
    main()
