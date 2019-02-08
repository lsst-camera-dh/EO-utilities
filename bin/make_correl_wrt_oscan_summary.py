#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.bias.correl_wrt_oscan import correl_wrt_oscan_summary

def main():
    """Hook for setup.py"""
    correl_wrt_oscan_summary.run()

if __name__ == '__main__':
    main()
