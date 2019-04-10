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
