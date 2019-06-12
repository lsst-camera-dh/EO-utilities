#!/usr/bin/env python

"""This module is just a command line interface to plot bias images"""

import glob

import lsst.pex.config as pexConfig

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions,\
    setup_parser, add_pex_arguments

from lsst.eo_utils.base.plot_utils import FigureDict


def get_files_by_slot(basepath):    
    """Make a mosaic of all the CCDs in a raft
    
    Parameters
    ----------
    basepath : `str` or `None`
        Base file name.

    Returns
    -------
    slot_dict : `dict` or `None`
        Filenames keyed by slot
    """
    if basepath is None:
        return None
    slot_dict = {slot:basepath.replace('SLOT', slot) for slot in ALL_SLOTS}
    return slot_dict


class PlotConfig(pexConfig.Config):
    """Configuration for Plotting"""
    infile = EOUtilOptions.clone_param('infile')
    outfile = EOUtilOptions.clone_param('outfile')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')

def main():
    """Hook for setup.py"""

    parser = setup_parser()
    add_pex_arguments(parser, PlotConfig)

    args = parser.parse_args()

    if args.outfile is None:
        output_file = args.infile.replace('SLOT', 'RFT').replace('.fits', '')
    else:
        output_file = args.outfile
        
    ccd_dict = get_files_by_slot(args.infile)
    bias_dict = get_files_by_slot(args.superbias)

    figs = FigureDict()

    if args.bias is not None:
        bias_subtract = True
    else:
        bias_subtract = False

    figs.plot_raft_mosaic('mosaic', ccd_dict, bias_subtract=bias_subtract,
                          bias_frames=bias_dict)

    figs.save_all(output_file)


if __name__ == '__main__':
    main()
