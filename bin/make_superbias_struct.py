#!/usr/bin/env python

"""This module is just a command line interface to plot profile structure in superbias frames"""

from lsst.eo_utils.bias.bias_struct import superbias_struct

def main():
    """Hook for setup.py"""
    superbias_struct.run()

if __name__ == '__main__':
    main()
