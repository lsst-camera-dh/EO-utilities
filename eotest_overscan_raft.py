"""
@brief Additional analysis on flat pair eotest
"""
import glob
import argparse
import astropy.io.fits as fits
import matplotlib.pyplot as plt
import os
from os.path import join
import numpy as np
import errno

from overscanTask import OverscanTask
from lsst.eotest.sensor import parse_geom_kwd, makeAmplifierGeometry
from deferredChargePlots import *
import lsst.eotest.image_utils as imutils

def main(directory, output_dir):

    ccd_names = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']

    try:
        os.makedirs(output_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    for sensor_id in ccd_names:
        print(sensor_id)

        ccd_output_dir = join(output_dir, sensor_id)
        try:
            os.makedirs(ccd_output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        ## Get flat and bias images
        flat_pair_dir = join(directory, 'flat_pair_raft_acq', 
                             'v0', '*', sensor_id)                         
        flat1_files = sorted(glob.glob(join(flat_pair_dir, '*flat1*.fits')))
        bias_files = sorted(glob.glob(join(flat_pair_dir, '*flat_bias*.fits')))

        ## Make a superbias 
        print("Making superbias")
        amp_geom = makeAmplifierGeometry(bias_files[0])
        oscan = amp_geom.serial_overscan
        bias_frame = join(output_dir, 
                          '{0}_superbias.fits'.format(sensor_id))
        imutils.superbias_file(bias_files[:4], oscan, bias_frame)
        
        ## Get amplifier gains
        with fits.open(flat1_files[0]) as hdulist:
            lsst_num = hdulist[0].header['LSST_NUM']
            datasec = parse_geom_kwd(hdulist[1].header['DATASEC'])
            xmin = datasec['xmin']
            xmax = datasec['xmax']                                     
        results = glob.glob(join(directory, 'collect_raft_results', 
                                 'v0', '*', 
                                 '{0}_eotest_results.fits'.format(lsst_num)))[0]
        with fits.open(results) as hdulist:
            gains_array = hdulist[1].data['GAIN']
            gains = dict((i+1, gains_array[i]) for i in range(16))

        ## Run overscan task
        overscantask = OverscanTask()
        overscantask.config.output_dir = ccd_output_dir
        output_file = overscantask.run(sensor_id, flat1_files, gains, 
                                       bias_frame=bias_frame)

        ## Make plots
        eper_plot(sensor_id, output_file, xmax=xmax, 
                  output_dir=ccd_output_dir)
        first_overscan_plot(sensor_id, output_file, xmax=xmax, 
                            output_dir=ccd_output_dir)
        cti_plot(sensor_id, output_file, xmax=xmax, 
                 output_dir=ccd_output_dir)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('eotest_dir', type=str, 
                        help='File path to eotest job harness directory')
    parser.add_argument('-o', '--output_dir', default='./', type=str,
                        help = "Output directory for FITs results.")
    args = parser.parse_args()

    directory = args.eotest_dir
    output_dir = args.output_dir
    
    main(directory, output_dir)

