#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias import bias_fft, bias_v_row, bias_struct,\
    oscan_amp_stack, correl_wrt_oscan, superbias, superbias_stats
from lsst.eo_utils.flat import ptc
from lsst.eo_utils.fe55 import fe55_gain


def main():
    """Hook for setup.py"""
    EO_TASK_FACTORY.parse_and_run()

if __name__ == '__main__':
    main()
