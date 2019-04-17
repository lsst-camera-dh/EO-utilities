#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.bias.superbias_stats import superbias_stats_summary

def main():
    """Hook for setup.py"""
    superbias_stats_summary.run()

if __name__ == '__main__':
    main()
