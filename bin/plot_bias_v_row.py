#!/usr/bin/env python

from lsst.eo_utils.config_utils import setup_parser
from lsst.eo_utils.bias_utils import run_plot_bias_v_row, ALL_SLOTS

def main():
    """Hook for setup.py"""
    argnames = ['raft', 'run', 'slots',
                'bias', 'mask', 'db', 'outdir']

    parser = setup_parser(argnames)
    args = parser.parse_args()
    arg_dict = args.__dict__.copy()

    raft = arg_dict.pop('raft')
    run_num = arg_dict.pop('run')
    slot_list = arg_dict.pop('slots')

    if slot_list is None:
        slot_list = ALL_SLOTS

    run_plot_bias_v_row(raft, run_num, slot_list, **arg_dict)


if __name__ == '__main__':
    main()
