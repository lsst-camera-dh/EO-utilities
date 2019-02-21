#!/usr/bin/env python

"""This module is just a command line interface to plot the
correlations between overscan regions for each pair of
amplifiers on a raft"""

from lsst.eo_utils.bias_utils import BiasAnalysisByRaft, plot_oscan_correl_raft

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts',
                'covar', 'db', 'outdir']

    functor = BiasAnalysisByRaft(plot_oscan_correl_raft, argnames)
    functor.run()

if __name__ == '__main__':
    main()
