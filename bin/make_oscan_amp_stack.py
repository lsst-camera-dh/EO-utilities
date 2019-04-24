#!/usr/bin/env python

"""This module is just a command line interface to plot a stacked image
of the overscan regions from several amplifiers, to look for
structured read noise"""

from lsst.eo_utils.bias.oscan_amp_stack import OscanAmpStackTask

def main():
    """Hook for setup.py"""
    OscanAmpStackTask.parseAndRun()

if __name__ == '__main__':
    main()
