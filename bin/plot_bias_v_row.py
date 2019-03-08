#!/usr/bin/env python

"""This module is just a command line interface to plot the unbiasing function
for bias images"""

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_bias_v_row_slot

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots',
                'bias', 'mask', 'db', 'butler_repo', 'outdir']

    functor = BiasAnalysisBySlot(plot_bias_v_row_slot, argnames)
    functor.run()

if __name__ == '__main__':
    main()
