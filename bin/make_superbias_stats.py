#!/usr/bin/env python

"""This module is just a command line interface to plot the statistics
from a set of superbias runs"""

from lsst.eo_utils.bias.superbias_stats import SuperbiasStatsTask

def main():
    """Hook for setup.py"""
    SuperbiasStatsTask.run()

if __name__ == '__main__':
    main()
