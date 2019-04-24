#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.bias.correl_wrt_oscan import CorrelWRTOScanSummaryTask

def main():
    """Hook for setup.py"""
    CorrelWRTOScanSummaryTask.parse_and_run()

if __name__ == '__main__':
    main()
