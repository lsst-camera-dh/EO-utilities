#!/usr/bin/env python

"""This module is just a command line interface to make superbias files"""

from lsst.eo_utils.bias.superbias import SuperbiasTask

def main():
    """Hook for setup.py"""
    SuperbiasTask.run()

if __name__ == '__main__':
    main()
