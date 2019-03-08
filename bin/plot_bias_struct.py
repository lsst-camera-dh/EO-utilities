#!/usr/bin/env python

"""This module is just a command line interface to plot profile structure in bias images"""

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_bias_struct_slot

def main():
    """Hook for setup.py"""

    argnames = ['run', 'rafts', 'slots',
                'bias', 'superbias',
                'std', 'mask', 'db', 'butler_repo', 'outdir']

    functor = BiasAnalysisBySlot(plot_bias_struct_slot, argnames)
    functor.run()


if __name__ == '__main__':
    main()
