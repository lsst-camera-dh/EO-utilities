#!/usr/bin/env python

"""This module is just a command line interface to plot profile structure in superbias frames"""

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_superbias_struct_slot

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots',
                'superbias', 'mask', 'std', 'db', 'butler_repo', 'outdir']

    functor = BiasAnalysisBySlot(plot_superbias_struct_slot, argnames)
    functor.run()

if __name__ == '__main__':
    main()
