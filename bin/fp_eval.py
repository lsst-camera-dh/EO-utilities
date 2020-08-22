#!/usr/bin/env python

"""This module contains provides to do simple arithmatic at the FP level"""

import sys

import glob

import shutil

import argparse

import numpy as np

from astropy.io import fits

ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
CORNER_SLOTS = ['SG0', 'SG1', 'SW0', 'SW1']


CORNER_RAFTS = ['R00', 'R04', 'R40', 'R44']
SCIENCE_RAFTS = ['R01', 'R02', 'R03',
                 'R10', 'R11', 'R12', 'R13', 'R14',
                 'R20', 'R21', 'R22', 'R23', 'R24',
                 'R30', 'R31', 'R32', 'R33', 'R34',
                 'R41', 'R42', 'R43']
BOT_RAFTS = SCIENCE_RAFTS + CORNER_RAFTS


def getSlotList(raftName):
    if raftName in CORNER_RAFTS:
        return CORNER_SLOTS
    return ALL_SLOTS


def fitsarith(inputlist, output, expression):

    if not inputlist:
        raise ValueError("Input is empty")

    hdus_in = [ fits.open(fin) for fin in inputlist ]
    use_expr = ""
    use_expr += expression
    n_in = len(hdus_in)

    for i in range(n_in):
        from_string = "@%i" % i
        to_string = "h[%i]" % i
        use_expr = use_expr.replace(from_string, to_string)

    n_hdu = len(hdus_in[0])

    shutil.copyfile(inputlist[0], output)

    for j in range(n_hdu):
        if type(hdus_in[0][j]) != fits.hdu.image.ImageHDU:
            continue
        h = [ hdus[j].data for hdus in hdus_in ]

        print(use_expr)
        data_output = eval(use_expr)
        fits.update(output, data_output, j, header=hdus_in[0][j].header)


def get_files(arglist, raft, slot):

    filenames = [ arg.format(raft=raft, slot=slot) for arg in arglist ]
    out = []
    for fname in filenames:
        files = glob.glob(fname)
        nfiles = len(files)
        if nfiles > 1:
            print("Warning, %i files match %s, taking first file" % (nfiles, fname))
        elif nfiles == 0:
            print("Warning, no files match %s." % (fname))                    
            return None
        out.append(files[0])
    return out
    
        

if __name__ == "__main__":
    # argument parser
    parser = argparse.ArgumentParser(prog='fp_arith')
    parser.add_argument('args', nargs='+', type=str, help="Patterns for image1files")
    parser.add_argument('-o', "--output", type=str, required=True, help="Pattern for output files")
    parser.add_argument('-e', "--expression", type=str, required=True, help="Mathematical expression, use @0, @1 etc. to refer to images")
    # unpack options
    options = parser.parse_args()

    for raft in BOT_RAFTS:
        raft_dict = {}
        slots = getSlotList(raft)
        for slot in slots:
            files = get_files(options.args, raft, slot)
            if files is None:
                continue
            outfile = options.output.format(raft=raft, slot=slot)    
            fitsarith(files, outfile, options.expression)
    
    
    
