#!/usr/bin/env python

"""This module is just a command line interface to plot the statistics
from a set of superbias runs"""

from lsst.eo_utils.bias.superbias_stats import superbias_stats

def main():
    """Hook for setup.py"""
    superbias_stats.run()

if __name__ == '__main__':
    main()
