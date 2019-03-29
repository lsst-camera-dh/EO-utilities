#!/usr/bin/env python

"""This module is just a command line interface to plot the
correlations between overscan regions for each pair of
amplifiers on a raft"""

from lsst.eo_utils.base.config_utils import STANDARD_RAFT_ARGS
from lsst.eo_utils.bias.analysis import BiasAnalysisByRaft, make_oscan_correl_raft

def main():
    """Hook for setup.py"""
    argnames = STANDARD_RAFT_ARGS + ['covar']

    functor = BiasAnalysisByRaft(make_oscan_correl_raft, argnames)
    functor.run()

if __name__ == '__main__':
    main()
