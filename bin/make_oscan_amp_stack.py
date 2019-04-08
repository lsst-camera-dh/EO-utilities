#!/usr/bin/env python

"""This module is just a command line interface to plot a stacked image
of the overscan regions from several amplifiers, to look for
structured read noise"""

from lsst.eo_utils.bias.bias_fft import oscan_amp_stack

def main():
    """Hook for setup.py"""
    oscan_amp_stack.run()

if __name__ == '__main__':
    main()
