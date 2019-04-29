#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils import base, bias, flat, fe55


def main():
    """Hook for setup.py"""
    EO_TASK_FACTORY.parse_and_run()

if __name__ == '__main__':
    main()
