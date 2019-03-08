#!/usr/bin/env python

"""This module is just a command line interface to plot bias images"""

from lsst.eo_utils.file_utils import FileRef
from lsst.eo_utils.config_utils import setup_parser
from lsst.eo_utils.plot_utils import FigureDict

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

    inRef = FileRef(args.input)
    if args.superbias is None:
        superbiasRef = None
    else:
        superbiasRef = FileRef(args.superbias)

    figs.plot_sensor("image", inRef, mask_files=[],
                     vmin=args.vmin, vmax=args.vmax,
                     bias=args.bias, superbias=superbiasRef,
                     subtract_mean=args.subtract_mean)
    figs.savefig("image", output_file)

    if args.stats_hist:
        figs.histogram_array("hist", inRef, mask_files=[],
                             bias=args.bias, superbias=superbiasRef,
                             xlabel="Counts", ylabel="Pixels / bin",
                             vmin=args.vmin, vmax=args.vmax,
                             nbins=args.nbins, region=None,
                             subtract_mean=args.subtract_mean)
        output_file_stat = output_file.replace('.png', '_hist.png')
        figs.savefig("hist", output_file_stat)


if __name__ == '__main__':
    main()
