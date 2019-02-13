#!/usr/bin/env python

from config_utils import setup_parser
from bias_utils import run_plot_oscan_correl

def main():
    """Hook for setup.py"""
    argnames = ['raft', 'run', 'covar', 'db', 'outdir']

    parser = setup_parser(argnames)
    args = parser.parse_args()
    arg_dict = args.__dict__.copy()

    raft = arg_dict.pop('raft')
    run_num = arg_dict.pop('run')

    run_plot_oscan_correl(raft, run_num, **arg_dict)


if __name__ == '__main__':
    main()
