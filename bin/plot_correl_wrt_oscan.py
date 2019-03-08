#!/usr/bin/env python

"""This module is just a command line interface to plot the correlaction between
the overscan and imaging regions in bias images"""

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_correl_wrt_oscan_slot

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots',
                'db', 'butler_repo', 'outdir']

    functor = BiasAnalysisBySlot(plot_correl_wrt_oscan_slot, argnames)
    functor.run()


if __name__ == '__main__':
    main()
