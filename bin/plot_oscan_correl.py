#!/usr/bin/env python

import argparse

from bias_utils import run_plot_oscan_correl
from file_utils import RD_ROOT_FOLDER, RAFT_ROOT_FOLDER


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--raft", default=None,
                        help="Raft Name")
    parser.add_argument("--run", default=None,
                        help="Data folder")
    parser.add_argument("--root_dir", default=None,
                        help="Root file path")
    parser.add_argument("--covar", action='store_true', default=False,
                        help="plot covariance")
    parser.add_argument("--rtype", default='raft',
                        help="Type of run")

    args = parser.parse_args()
    arg_dict = args.__dict__.copy()

    raft = arg_dict.pop('raft')
    run_num = arg_dict.pop('run')

    root_data_path = arg_dict.pop('root_dir')
    if root_data_path is None:
        if args.rtype == 'RD':
            root_data_path = RD_ROOT_FOLDER
        elif args.rtype == 'raft':
            root_data_path = RAFT_ROOT_FOLDER
    arg_dict['root_dir'] = root_data_path

    run_plot_oscan_correl(raft, run_num, **arg_dict)
