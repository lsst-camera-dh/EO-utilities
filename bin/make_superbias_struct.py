#!/usr/bin/env python

"""This module is just a command line interface to plot profile structure in superbias frames"""

from lsst.eo_utils.bias.bias_struct import SuperbiasStructTask

def main():
    """Hook for setup.py"""
    SuperbiasStructTask.parse_and_run()

if __name__ == '__main__':
    main()
