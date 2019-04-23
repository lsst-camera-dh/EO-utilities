#!/usr/bin/env python

"""This module is just a command line to get summary gain data from fe55 analyses"""

from lsst.eo_utils.fe55.fe55_gain import fe55_gain_summary

def main():
    """Hook for setup.py"""
    fe55_gain_summary.run()

if __name__ == '__main__':
    main()
