import glob
import argparse
import astropy.io.fits as fits
import os

from lsst.eotest.sensor import SpotTask
from lsst.eotest.sensor import parse_geom_kwd, makeAmplifierGeometry

def main(sensor_id, infile, bias_frame=None, output_dir='./'):

    gains = dict((i+1, 1.0) for i in range(16))
    spottask = SpotTask()
    spottask.config.output_dir = output_dir
    spottask.run(sensor_id, infile, gains, bias_frame=bias_frame)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('sensor_id', type=str)
    parser.add_argument('infile', type=str)
    parser.add_argument('-b', '--bias_frame', type=str, default=None)
    parser.add_argument('-o', '--output_dir', type=str, default='./')
    args = parser.parse_args()

    sensor_id = args.sensor_id
    infile = args.infile
    bias_frame = args.bias_frame
    output_dir = args.output_dir

    main(sensor_id, infile, bias_frame=bias_frame, output_dir=output_dir)
