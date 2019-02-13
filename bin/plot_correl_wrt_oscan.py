#!/usr/bin/env python

from lsst.eo_utils.config_utils import setup_parser
from lsst.eo_utils.bias_utils import run_plot_correl_wrt_oscan, ALL_SLOTS


def main():
    """Hook for setup.py"""
    argnames = ['raft', 'run', 'slots',
                'db', 'outdir']

    parser = setup_parser(argnames)
    args = parser.parse_args()
    arg_dict = args.__dict__.copy()

    raft = arg_dict.pop('raft')
    run_num = arg_dict.pop('run')
    slot_list = arg_dict.pop('slots')

    if slot_list is None:
        slot_list = ALL_SLOTS

    run_plot_correl_wrt_oscan(raft, run_num, slot_list, **arg_dict)


if __name__ == '__main__':
    main()
