#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils import base, bias, flat, fe55, sflat, dark, qe, ppump, meta

MODULE_LOCATION_DICT = dict(base=base.__file__,
                            bias=bias.__file__,
                            flat=flat.__file__,
                            fe55=fe55.__file__,
                            sflat=sflat.__file__,
                            dark=dark.__file__,
                            qe=qe.__file__,
                            ppump=ppump.__file__,
                            meta=meta.__file__)

def main():
    """Hook for setup.py"""
    EO_TASK_FACTORY.parse_and_run()

if __name__ == '__main__':
    main()
