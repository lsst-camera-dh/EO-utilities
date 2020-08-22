#!/usr/bin/env python

"""This module contains provides to do simple arithmatic at the FP level"""

import sys

import glob

import shutil

import argparse

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


def fitsarith(input1, input2, output, operation, const1=None, const2=None):
    # read input files - must have same extension structure!
    hdu1 = fits.open(input1)
    hdu2 = fits.open(input2)
    # build output file by copying input1
    shutil.copyfile(input1,output)
    # loop through extensions, find image extensions only, and do arithmetic
    for i in range(len(hdu1)):
        exten1 = hdu1[i]
        exten2 = hdu2[i]     
        if type(exten1) != fits.hdu.image.ImageHDU:
            continue
        if const1 is None:
            data1 = exten1.data
        else:
            data1 = const1 * exten1.data
        if const2 is None:
            data2 = exten2.data
        else:
            data2 = const2* exten2.data
        if operation == "+":
            data_output = data1 + data2
        elif operation == "-":
            data_output = data1 - data2
        elif operation == "*":
            data_output = data1 * data2
        elif operation == "/":
            data_output = data1 / data2
        else:
            raise ValueError("Unknown operator %s" % operation)
        # update this extension in output fits file
        fits.update(output,data_output,i,header=exten1.header)



if __name__ == "__main__":
    # argument parser
    parser = argparse.ArgumentParser(prog='fp_arith')
    parser.add_argument('-i1', "--input1", type=str, required=True, help="Pattern for image1 files")
    parser.add_argument('-i2', "--input2", type=str, required=True, help="Pattern for image2 files")
    parser.add_argument('-c1', "--const1", type=float, default=None, help="Constant prefactor for image1")
    parser.add_argument('-c2', "--const2", type=float, default=None, help="Constant prefactor for image2")
    parser.add_argument('-out', "--output", type=str, required=True, help="Pattern for output files")
    parser.add_argument('-op', "--operation", type=str, required=True, help="Operation, choices are: +,-,*,/")
    # unpack options
    options = parser.parse_args()

    for raft in BOT_RAFTS:
        raft_dict = {}
        slots = getSlotList(raft)
        for slot in slots:
            slotglob1 = options.input1.format(raft=raft, slot=slot)
            files1 = glob.glob(slotglob1)
            nfiles1 = len(files1)
            if nfiles1 > 1:
                print("Warning, %i files match %s, taking first file" % (nfiles1, slotglob1))
            elif nfiles1 == 0:
                print("Warning, no files match %s." % (slotglob1))                    
                continue
            val1 = files1[0]
            slotglob2 = options.input2.format(raft=raft, slot=slot)
            files2 = glob.glob(slotglob2)
            nfiles2 = len(files2)
            if nfiles2 > 1:
                print("Warning, %i files match %s, taking first file" % (nfiles2, slotglob2))
            elif nfiles2 == 0:
                print("Warning, no files match %s." % (slotglob2))                    
                continue
            val2 = files2[0]
            outfile = options.output.format(raft=raft, slot=slot)
    
            print(val1, val2, outfile, options.operation, options.const1, options.const2)
            fitsarith(val1, val2, outfile, options.operation, options.const1, options.const2)
        
    
    
    
