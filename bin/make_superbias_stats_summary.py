#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.bias.superbias_stats import SuperbiasSummaryTask

def main():
    """Hook for setup.py"""
    SuperbiasSummaryTask.parseAndRun()

if __name__ == '__main__':
    main()
