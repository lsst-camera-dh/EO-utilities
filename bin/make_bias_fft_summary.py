#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.bias.bias_fft import BiasFFTSummaryTask

def main():
    """Hook for setup.py"""
    BiasFFTSummaryTask.parseAndRun()

if __name__ == '__main__':
    main()
