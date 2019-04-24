#!/usr/bin/env python

"""This module is just a command line interface to plot the data from the bias images"""

from lsst.eo_utils.bias.bias_data import bias_data

def main():
    """Hook for setup.py"""
    bias_data.parse_and_run()

if __name__ == '__main__':
    main()
