#!/usr/bin/env python

"""This module is just a command line interface to plot bias images"""

import lsst.pex.config as pexConfig

from lsst.eo_utils.base.config_utils import EOUtilOptions,\
    setup_parser, add_pex_arguments
from lsst.eo_utils.base.image_utils import get_ccd_from_id
from lsst.eo_utils.base.plot_utils import FigureDict

class PlotConfig(pexConfig.Config):
    """Configuration for Plotting"""
    input = EOUtilOptions.clone_param('input')
    output = EOUtilOptions.clone_param('output')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    vmin = EOUtilOptions.clone_param('vmin')
    vmax = EOUtilOptions.clone_param('vmax')
    nbins = EOUtilOptions.clone_param('nbins')
    subtract_mean = EOUtilOptions.clone_param('subtract_mean')
    stats_hist = EOUtilOptions.clone_param('stats_hist')

def main():
    """Hook for setup.py"""

    parser = setup_parser()
    add_pex_arguments(parser, PlotConfig)

    args = parser.parse_args()

    if args.output is None:
        output_file = args.input.replace('.fits', '.png')
    else:
        output_file = args.output

    ccd = get_ccd_from_id(None, args.input, mask_files=[])
    if args.superbias is not None:
        superbias_frame = get_ccd_from_id(None, args.superbias, mask_files=[])
    else:
        superbias_frame = None

    figs = FigureDict()

    figs.plot_sensor("img", None, ccd,
                     vmin=args.vmin, vmax=args.vmax,
                     bias=args.bias, superbias_frame=superbias_frame,
                     subtract_mean=args.subtract_mean)

    if args.stats_hist:
        figs.histogram_array("hist", None, ccd,
                             bias=args.bias, superbias_frame=superbias_frame,
                             xlabel="Counts", ylabel="Pixels / bin",
                             vmin=args.vmin, vmax=args.vmax,
                             nbins=args.nbins, region=None,
                             subtract_mean=args.subtract_mean)

    figs.save_all(output_file.replace('.fits', ''))


if __name__ == '__main__':
    main()
