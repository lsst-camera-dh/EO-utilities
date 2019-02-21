#!/usr/bin/env python

from lsst.eo_utils.bias_utils import BiasAnalysisBySlot, plot_correl_wrt_oscan_slot


def main():
    """Hook for setup.py"""
    argnames = ['run', 'rafts', 'slots',
                'db', 'outdir']

    functor = BiasAnalysisBySlot(plot_correl_wrt_oscan_slot, argnames)
    functor.run()


if __name__ == '__main__':
    main()
