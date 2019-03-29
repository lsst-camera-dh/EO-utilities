#!/usr/bin/env python

"""This module is just a command line interface to plot a stacked image
of the overscan regions from several amplifiers, to look for
structured read noise"""

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS
from lsst.eo_utils.bias.analysis import BiasAnalysisBySlot, make_oscan_amp_stack_slot

def main():
    """Hook for setup.py"""
    argnames = STANDARD_SLOT_ARGS + ['mask', 'bias', 'superbias']

    functor = BiasAnalysisBySlot(make_oscan_amp_stack_slot, argnames)
    functor.run()

if __name__ == '__main__':
    main()
