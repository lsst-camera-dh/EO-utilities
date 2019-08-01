#!/usr/bin/env python

"""This module is just a command line interface to plot the FFT of bias images"""

import sys

import argparse

from lsst.eo_utils import EOUtils

from lsst.eo_utils import base, bias, flat, fe55, sflat, dark, qe, ppump

MODULE_LIST = [base, bias, flat, fe55, sflat, dark, qe, ppump]

def main():
    """Hook for setup.py"""
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--task", default=None,
                        help="Task name")
    parser.add_argument("-i", "--input", default=None,
                        help="Text file with raft and run numbers")
    parser.add_argument("--list", action='store_true', default=False,
                        help="List Missing Files")
    parser.add_argument("--found", action='store_true', default=False,
                        help="List Found Files")
    args = parser.parse_args()

    manager = EOUtils()

    if args.task is None:
        tasks = manager.get_task_names()
    else:
        tasks = [args.task]

    for task in tasks:
        found, missing = manager.check_task_files(task, args.input)

        sys.stdout.write("Dataset %s:%s: found %i, missing %i.\n" % (args.input, task,
                                                                     len(found), len(missing)))
        if args.list and missing:
            for mfile in missing:
                sys.stdout.write("  %s\n" % mfile)
        if args.found and found:
            for ffile in found:
                sys.stdout.write("  + %s\n" % ffile)



if __name__ == '__main__':
    main()
