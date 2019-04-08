#!/usr/bin/env python

"""This module is just a command line interface to plot the unbiasing function
for bias images"""

from lsst.eo_utils.bias.bias_v_row import bias_v_row

def main():
    """Hook for setup.py"""
    bias_v_row.run()

if __name__ == '__main__':
    main()
