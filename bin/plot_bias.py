#!/usr/bin/env python

"""This module is just a command line interface to plot bias images"""

from lsst.eo_utils.base.config_utils import setup_parser
from lsst.eo_utils.base.plot_utils import FigureDict

def main():
    """Hook for setup.py"""
    argnames = ['input', 'output', 'bias', 'superbias',
                'vmin', 'vmax', 'nbins',
                'subtract_mean', 'stats_hist']

    parser = setup_parser(argnames)
    args = parser.parse_args()

    if args.output is None:
        output_file = args.input.replace('.fits', '.png')
    else:
        output_file = args.output


    figs = FigureDict()

    figs.plot_sensor("img", args.input, mask_files=[],
                     vmin=args.vmin, vmax=args.vmax,
                     bias=args.bias, superbias=args.superbias,
                     subtract_mean=args.subtract_mean)

    if args.stats_hist:
        figs.histogram_array("hist", args.input, mask_files=[],
                             bias=args.bias, superbias=args.superbias,
                             xlabel="Counts", ylabel="Pixels / bin",
                             vmin=args.vmin, vmax=args.vmax,
                             nbins=args.nbins, region=None,
                             subtract_mean=args.subtract_mean)

    figs.save_all(output_file.replace('.fits', ''))


if __name__ == '__main__':
    main()
