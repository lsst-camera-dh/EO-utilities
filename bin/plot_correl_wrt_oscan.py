#!/usr/bin/env python

import argparse
from bias_utils import run_plot_correl_wrt_oscan, ALL_SLOTS

DEFAULT_ROOT_DIR = '/gpfs/slac/lsst/fs1/g/data/jobHarness/jh_archive-test/LCA-11021_RTM/'

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--raft", default=None,
                        help="Raft Name")
    parser.add_argument("--run", default=None,
                        help="Run number")
    parser.add_argument("--slots", default=None, action="append",
                        help="Slot number")
    parser.add_argument("--root_dir", default=DEFAULT_ROOT_DIR,
                        help="Root file path")

    args = parser.parse_args()
    arg_dict = args.__dict__.copy()

    raft = arg_dict.pop('raft')
    run_num = arg_dict.pop('run')
    slot_list = arg_dict.pop('slots')

    if slot_list is None:
        slot_list = ALL_SLOTS

    run_plot_correl_wrt_oscan(raft, run_num, slot_list, **arg_dict)
