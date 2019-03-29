#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS
from lsst.eo_utils.bias.analysis import BiasAnalysisBySlot, make_bias_fft_slot

def main():
    """Hook for setup.py"""

    argnames = STANDARD_SLOT_ARGS + ['mask', 'bias', 'superbias', 'std']

    functor = BiasAnalysisBySlot(make_bias_fft_slot, argnames)
    functor.run()

if __name__ == '__main__':
    main()
