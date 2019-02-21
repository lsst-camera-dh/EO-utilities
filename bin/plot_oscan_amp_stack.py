#!/usr/bin/env python

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_oscan_amp_stack_slot

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots',
                'bias', 'superbias', 'mask',
                'db', 'outdir']

    functor = BiasAnalysisBySlot(plot_oscan_amp_stack_slot, argnames)
    functor.run()

if __name__ == '__main__':
    main()
