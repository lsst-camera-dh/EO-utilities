#!/usr/bin/env python

from config_utils import setup_parser
from plot_utils import plot_sensor, histogram_array

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

    fig = plot_sensor(args.input, mask_files=[],
                      vmin=args.vmin, vmax=args.vmax,
                      bias=args.bias, superbias=args.superbias,
                      subtract_mean=args.subtract_mean)
    fig[0].savefig(output_file)

    if args.stats_hist:
        fig_stat = histogram_array(args.input, mask_files=[],
                                   bias=args.bias, superbias=args.superbias,
                                   xlabel="Counts", ylabel="Pixels / bin",
                                   vmin=args.vmin, vmax=args.vmax,
                                   nbins=args.nbins, region=None,
                                   subtract_mean=args.subtract_mean)
        output_file_stat = output_file.replace('.png', '_hist.png')
        fig_stat[0].savefig(output_file_stat)


if __name__ == '__main__':
    main()
