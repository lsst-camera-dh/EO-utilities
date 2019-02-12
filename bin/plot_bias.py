#!/usr/bin/env python

import argparse
from plot_utils import plot_sensor, histogram_array


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default=None,
                        help="Input file")
    parser.add_argument("-o", "--output", default=None,
                        help="Output file")
    parser.add_argument("--vmin", type=float, default=-10.,
                        help="Color scale min value")
    parser.add_argument("--vmax", type=float, default=10.,
                        help="Color scale max value")
    parser.add_argument("--nbins", type=int, default=200,
                        help="Number of bins to use for stats hist")
    parser.add_argument("--subtract_mean", default=False, action='store_true',
                        help="Subtract mean value")
    parser.add_argument("--bias", default=None,
                        help="Bias Method")
    parser.add_argument("--superbias", default=None,
                        help="Superbias file")
    parser.add_argument("--stats_hist", default=False, action='store_true',
                        help="Make plot of histogram")

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
