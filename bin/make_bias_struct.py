#!/usr/bin/env python

"""This module is just a command line interface to plot profile structure in bias images"""

from lsst.eo_utils.bias.bias_struct import bias_struct

def main():
    """Hook for setup.py"""
    bias_struct.run()


if __name__ == '__main__':
    main()
