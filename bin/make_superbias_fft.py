#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of superbias frames"""

from lsst.eo_utils.bias.bias_fft import SuperbiasFFTTask

def main():
    """Hook for setup.py"""
    SuperbiasFFTTask.parseAndRun()

if __name__ == '__main__':
    main()
