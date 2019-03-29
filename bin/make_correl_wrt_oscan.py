#!/usr/bin/env python

"""This module is just a command line interface to plot the correlaction between
the overscan and imaging regions in bias images"""

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS
from lsst.eo_utils.bias.analysis import BiasAnalysisBySlot, make_correl_wrt_oscan_slot

def main():
    """Hook for setup.py"""

    argnames = STANDARD_SLOT_ARGS + ['mask']

    functor = BiasAnalysisBySlot(make_correl_wrt_oscan_slot, argnames)
    functor.run()


if __name__ == '__main__':
    main()
