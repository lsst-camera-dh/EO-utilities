#!/usr/bin/env python

import argparse
from plot_utils import plot_sensor


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
    parser.add_argument("--subtract_mean", default=False, action='store_true',
                        help="Subtract mean value")
    parser.add_argument("--bias", default=None,
                        help="Bias Method")

    args = parser.parse_args()

    if args.output is None:
        output_file = args.input.replace('.fits', '.png')
    else:
        output_file = args.output

    fig, axs = plot_sensor(args.input, mask_files=[],
                           vmin=args.vmin, vmax=args.vmax,
                           bias_method=args.bias,
                           subtract_mean=args.subtract_mean)

    fig.savefig(output_file)
