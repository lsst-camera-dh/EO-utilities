#!/usr/bin/env python

"""This module is just a command line interface to plot a stacked image
of the overscan regions from several amplifiers, to look for
structured read noise"""

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_oscan_amp_stack_slot

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots',
                'bias', 'superbias', 'mask',
                'butler_repo', 'outdir']

    functor = BiasAnalysisBySlot(plot_oscan_amp_stack_slot, argnames)
    functor.run()

if __name__ == '__main__':
    main()
