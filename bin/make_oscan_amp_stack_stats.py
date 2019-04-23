#!/usr/bin/env python

"""This module is just a command line interface to plot a stacked image
of the overscan regions from several amplifiers, to look for
structured read noise"""

from lsst.eo_utils.bias.oscan_amp_stack import OscanAmpStackStatsTask

def main():
    """Hook for setup.py"""
    OscanAmpStackStatsTask.run()

if __name__ == '__main__':
    main()
