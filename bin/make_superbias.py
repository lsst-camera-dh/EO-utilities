#!/usr/bin/env python

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, make_superbias_slot

def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots', 'bias', 'stat', 'plot',
                'skip', 'stats_hist', 'mask', 'db', 'outdir']

    functor = BiasAnalysisBySlot(make_superbias_slot, argnames)
    functor.run()


if __name__ == '__main__':
    main()
