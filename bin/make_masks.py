#!/usr/bin/env python

"""This module is just a command line interface to make mask files"""

from lsst.eo_utils.base.mask_analysis import MaskAnalysisBySlot, make_mask


def main():
    """Hook for setup.py"""
    argnames = ['run', 'slots', 'butler_repo', 'outdir']

    functor = MaskAnalysisBySlot(make_mask, argnames)
    functor.run_analysis()


if __name__ == '__main__':
    main()
