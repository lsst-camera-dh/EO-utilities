#!/usr/bin/env python

"""This module is just a command line interface to plot the unbiasing function
for bias images"""

from lsst.eo_utils.bias.bias_v_row import BiasVRowTask

def main():
    """Hook for setup.py"""
    BiasVRowTask.parse_and_run()

if __name__ == '__main__':
    main()
