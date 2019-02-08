#!/usr/bin/env python

import argparse
from bias_utils import run_make_superbias, ALL_SLOTS

DEFAULT_ROOT_DIR = '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM/'

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--raft", default=None,
                        help="Raft Name")
    parser.add_argument("--run", default=None,
                        help="Run id")
    parser.add_argument("--slots", default=None, action="append",
                        help="Slot number")
    parser.add_argument("--bias", default='spline',
                        help="Method to unbias individual images")
    parser.add_argument("--stat", default='median',
                        help="Statistic to use to stack images")
    parser.add_argument("--plot", default=False, action='store_true',
                        help="Make plots")
    parser.add_argument("--skip", default=False, action='store_true',
                        help="Don't actually make the superbias")
    parser.add_argument("--stats_hist", default=False, action='store_true',
                        help="Make plot of histogram")
    parser.add_argument("--mask", default=False, action='store_true',
                        help="Use masks")
    parser.add_argument("--root_dir", default=DEFAULT_ROOT_DIR,
                        help="Root file path")

    args = parser.parse_args()
    arg_dict = args.__dict__.copy()

    raft = arg_dict.pop('raft')
    run_num = arg_dict.pop('run')
    slot_list = arg_dict.pop('slots')

    if slot_list is None:
        slot_list = ALL_SLOTS

    run_make_superbias(raft, run_num, slot_list, **arg_dict)
