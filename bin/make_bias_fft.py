#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.bias.bias_fft import BiasFFTTask

def main():
    """Hook for setup.py"""
    BiasFFTTask.parse_and_run()

if __name__ == '__main__':
    main()
