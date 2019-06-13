#!/usr/bin/env python
"""Specialize template code for a particular task"""

import os

import sys

import argparse

from collections import OrderedDict


def specialize_file(infile, outfile, trans_dict):
    """Perform a series of replacements to turn a template file into usable code

    Parameters
    ----------
    infile : `str`
        The input file
    outfile : `str` or `None`
        The output file, None for stdout
    trans_dict : `dict`
        The translation dictionary
    """
    fin = open(infile)
    if outfile is None:
        fout = sys.stdout
    else:
        fout = open(outfile, 'w')

    line = fin.readline()

    while line:
        outline = line
        for key, val in trans_dict.items():
            outline = outline.replace(key, val)
        fout.write(outline)
        line = fin.readline()


def main():
    """Hook for setup.py"""

    parser = argparse.ArgumentParser()

    parser.add_argument('-l', "--level", type=str, default='slot',
                        help="Level of analysis [slot, table, raft, summary]")

    parser.add_argument('-t', "--type", type=str, default='bias',
                        help="Type of analysis [bias, flat, dark ...]")

    parser.add_argument('-n', "--name", type=str, default=None,
                        help="Output class name")

    parser.add_argument('-s', "--suffix", type=str, default=None,
                        help="Output file suffix, required")

    parser.add_argument('-o', "--output", type=str, default=None,
                        help="Output filename")

    args = parser.parse_args()

    tmpl_dir = __file__.replace('bin/specialize_code.py', 'templates')

    tmpl_file = os.path.join(tmpl_dir, '%s_analysis.py' % args.level)

    trans_dict = OrderedDict(tmplsuffix=args.suffix,
                             TMPL=args.type.upper(),
                             Tmpl=args.type.capitalize(),
                             tmpl=args.type.lower(),
                             Template=args.name)

    specialize_file(tmpl_file, args.output, trans_dict)


if __name__ == '__main__':
    main()
