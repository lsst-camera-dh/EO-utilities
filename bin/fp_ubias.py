#!/usr/bin/env python

"""This module contains provides to do simple arithmatic at the FP level"""

import sys

import glob

import shutil

import argparse

from astropy.io import fits

from lsst.eo_utils.base.image_utils import unbias_amp, get_amp_list, get_ccd_from_id, get_geom_regions,\
    get_raw_image, get_amp_offset

ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
CORNER_SLOTS = ['SG0', 'SG1', 'SW0', 'SW1']


CORNER_RAFTS = ['R00', 'R04', 'R40', 'R44']
SCIENCE_RAFTS = ['R01', 'R02', 'R03',
                 'R10', 'R11', 'R12', 'R13', 'R14',
                 'R20', 'R21', 'R22', 'R23', 'R24',
                 'R30', 'R31', 'R32', 'R33', 'R34',
                 'R41', 'R42', 'R43']
BOT_RAFTS = SCIENCE_RAFTS + CORNER_RAFTS


def get_file(pattern, raft, slot):

    fname = pattern.format(raft=raft, slot=slot)
    files = glob.glob(fname)
    nfiles = len(files)
    if nfiles > 1:
        print("Warning, %i files match %s, taking first file" % (nfiles, fname))
    elif nfiles == 0:
        return None
    return files[0]

    
def getSlotList(raftName):
    if raftName in CORNER_RAFTS:
        return CORNER_SLOTS
    return ALL_SLOTS


def unbias(input_file, output_file, bias_method, bias_method_col=None, superbias_file=None):
    # build output file by copying input
    shutil.copyfile(input_file, output_file)

    ccd = get_ccd_from_id(None, input_file, [])
    hdulist = fits.open(input_file)
    
    if superbias_file is not None:
        superbias_ccd = get_ccd_from_id(None, superbias_file, [])
    else:
        superbias_ccd = None

    amps = get_amp_list(ccd)
    offset = get_amp_offset(ccd, superbias_ccd)

    for i, amp in enumerate(amps):
        regions = get_geom_regions(ccd, amp)
        serial_oscan = regions['serial_overscan']
        parallel_oscan = regions['parallel_overscan']
        img = get_raw_image(ccd, amp)
        if superbias_ccd is not None:
            superbias_im = get_raw_image(superbias_frame, amp + offset)
        else:
            superbias_im = None
        image = unbias_amp(img, serial_oscan, bias_type=bias_method, superbias_im=superbias_im, bias_type_col=bias_method_col, parallel_oscan=parallel_oscan)
        fits.update(output_file, image.image.array, amp, header=hdulist[amp].header)



if __name__ == "__main__":
    # argument parser
    parser = argparse.ArgumentParser(prog='fp_arith.py')
    parser.add_argument('-i', "--input", type=str, required=True, help="Pattern for image files")
    parser.add_argument('-s', "--superbias", type=str, default=None, help="Pattern for superbias files")
    parser.add_argument('-b', "--bias", type=str, default='None', help="Method for se")
    parser.add_argument('-c', "--bias_col", type=str, default='None', help="Method for parallel overscan subtraction")
    parser.add_argument('-o', "--output", type=str, required=True, help="Pattern for output files")
    parser.add_argument('--rafts', type=str, action='append', default=None, help="Rafts to include [All], can be used multiple times")
    parser.add_argument('--slots', type=str, action='append', default=None, help="Slots to include [All], can be used multiple times")    
    
    # unpack options
    options = parser.parse_args()

    if options.rafts is None:
        rafts = BOT_RAFTS
    else:
        rafts = options.rafts
    for raft in rafts:
        sys.stdout.write("%s" % raft)
        sys.stdout.flush()
        raft_dict = {}
        if options.slots is None:
            slots = getSlotList(raft)
        else:
            slots = options.slots
        for slot in slots:
            input_file = get_file(options.input, raft, slot)
            output_file = options.output.format(raft=raft, slot=slot)
            if options.superbias is not None:
                sb_file = get_file(options.superbias, raft, slot)
            else:
                sb_file = None
            if input_file is None:
                sys.stdout.write('x')
                sys.stdout.flush()
                continue
            sys.stdout.write('.')
            sys.stdout.flush()
            outfile = options.output.format(raft=raft, slot=slot)    
            unbias(input_file, output_file, bias_method=options.bias, bias_method_col=options.bias_col, superbias_file=sb_file)
            
    sys.stdout.write('!\n')
    
   
