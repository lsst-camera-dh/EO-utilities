#!/usr/bin/env python

"""This module is just a command line interface to plot profile structure in bias images"""

from lsst.eo_utils.bias.bias_struct import BiasStructTask

def main():
    """Hook for setup.py"""
    BiasStructTask.run()


if __name__ == '__main__':
    main()
