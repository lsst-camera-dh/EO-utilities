#!/usr/bin/env python

"""This module is just a command line interface to make superbias files"""

from lsst.eo_utils.bias.superbias import superbias

def main():
    """Hook for setup.py"""
    superbias.run()

if __name__ == '__main__':
    main()
