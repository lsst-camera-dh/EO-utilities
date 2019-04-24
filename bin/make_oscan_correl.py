#!/usr/bin/env python

"""This module is just a command line interface to plot the
correlations between overscan regions for each pair of
amplifiers on a raft"""


from lsst.eo_utils.bias.oscan_correl import OscanCorrelTask

def main():
    """Hook for setup.py"""
    OscanCorrelTask.parse_and_run()

if __name__ == '__main__':
    main()
