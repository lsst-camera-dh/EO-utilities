#!/usr/bin/env python

"""This module is just a command line interface to make superbias files"""

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS
from lsst.eo_utils.bias.analysis import BiasAnalysisBySlot, make_superbias_slot

def main():
    """Hook for setup.py"""
    argnames = STANDARD_SLOT_ARGS + ['mask', 'bias', 'stat', 'stats_hist']

    functor = BiasAnalysisBySlot(make_superbias_slot, argnames)
    functor.run(acq_types=["DARK", "FLAT", "FE55"])


if __name__ == '__main__':
    main()
