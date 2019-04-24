#!/usr/bin/env python

"""This module is just a command line interface to plot the correlaction between
the overscan and imaging regions in bias images"""

from lsst.eo_utils.bias.correl_wrt_oscan import CorrelWRTOScanTask

def main():
    """Hook for setup.py"""
    CorrelWRTOScanTask.parseAndRun()

if __name__ == '__main__':
    main()
