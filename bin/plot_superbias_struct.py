#!/usr/bin/env python

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_superbias_struct_slot

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots',
                'superbias', 'mask', 'std', 'db', 'outdir']

    functor = BiasAnalysisBySlot(plot_superbias_struct_slot, argnames)
    functor.run()

if __name__ == '__main__':
    main()
