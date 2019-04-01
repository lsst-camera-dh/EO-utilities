#!/usr/bin/env python
from __future__ import print_function

import matplotlib.pyplot as plt
import numpy as np
import argparse
import logging
import sys

from astropy.io import fits
from os.path import join
from scipy.ndimage.filters import gaussian_filter
from scipy import optimize
from glob import glob
from copy import deepcopy

def spot_mask(amp, ay, ax, r=100):
    """Mask amplifier except for spot at given coordinates."""

    ny, nx = amp.shape
    
    y, x = np.ogrid[-ay:ny-ay, -ax:nx-ax]
    mask = x*x + y*y >= r*r
    
    spot = np.ma.MaskedArray(amp, mask)
    return spot

def find_spot(amp, sigma=50, threshold=30000):
    """Find the center of the aggressor spot and return coordinates."""
    
    ## Gaussian filter using the set radius
    blurred = gaussian_filter(amp, sigma=sigma)
    
    y, x = np.unravel_index(blurred.argmax(), blurred.shape)
    
    ## Check mean to ensure a spot is found
    candidate_spot = spot_mask(amp, y, x, r=50)
    
    if np.mean(candidate_spot) > threshold:
        return y, x
    else:
        return None ## Maybe change to an error so can try/except in loop

def stamp(amp, ay, ax, l=300):
    """Create a 300x300 postage stamp at a given position on an amplifier."""
    
    maxy, maxx = amp.shape

    ## Truncate at amplifier edges
    if ay-l//2 < 0: 
        y0 = 0
    else:
        y0 = ay-l//2
    if ay+l//2 >= maxy: 
        y1 = maxy
    else:
        y1 = ay+l//2
    if ax-l//2 < 0: 
        x0 = 0
    else:
        x0 = ax-l//2
    if ax+l//2 >= maxx: 
        x1 = maxx
    else:
        x1 = ax+l//2

    stamp = deepcopy(amp[y0:y1, x0:x1])

    return stamp

def victim_model(var_array, aggressor):
    """Make a model of victim postage stamp."""
    
    # Get coefficients
    xtalk_signal = var_array[0]
    bias = var_array[1]
    tilty = var_array[2]
    tiltx = var_array[3]

    Y, X = np.mgrid[:aggressor.shape[0], :aggressor.shape[1]]
    model = xtalk_signal*aggressor + tilty*Y + tiltx*X + bias

    return model

def model_error(var_array, aggressor, victim):
    """Calculate sum of square error between victim and model."""
    
    model = victim_model(var_array, aggressor)
    return np.square(model-victim).sum()

def get_amp_pos(ampno):
    """Convert xtalk matrix index to CCD ID and amplifier number."""

    raft_ccds = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
    ccd = int(ampno/16)
    ccd_id = raft_ccds[ccd] 
    amp = ampno-16*ccd+1

    return ccd_id, amp

def main(image_dir = './', length=200, sigma=50, num_pos=36, 
         num_aggressors_per_position=4, num_iterations=5):

    ## Logging
    logger = logging.getLogger('xtalk')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    hdlr = logging.FileHandler(join(image_dir, 'xtalk_analysis.log'))
    hdlr.setFormatter(formatter)
    hdlr.setLevel(logging.INFO)

    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)

    ## Arrays to hold the output
    xtalk_array = np.zeros((144, 144))               # Xtalk signal result array
    background_array = np.zeros((144, 144))          # Background result array
    tilty_array = np.zeros((144, 144))               # Tilt Y result array
    tiltx_array = np.zeros((144, 144))               # Tilt X result array
    error_array = np.zeros((144, 144))               # Xtalk results error array
    lookup_dict = {}

    ## Get CCD amplifier shape parameters
    raft_ccds = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
    example_file = glob(join(image_dir, 'S00', '*.fits'))[0]
    example_image = fits.open(example_file)
    datasec = example_image[1].header['DATASEC']
    example_image.close()

    xslice, yslice = datasec[1:-1].split(',')
    xlow, xhigh = xslice.split(':')
    ylow, yhigh = yslice.split(':')

    xlow = int(xlow)
    xhigh = int(xhigh)
    ylow = int(ylow)
    yhigh = int(yhigh)

    ## Loop over each position of the xtalk projector
    for pos in range(num_pos):

        logger.debug("Starting position {0:03d}".format(pos))
        print("Starting position {0:03d}".format(pos))

        raft_array = np.zeros((144, yhigh-ylow, xhigh-xlow))

        ## Populate array of every ccd amplifier
        for ccd, raft_ccd in enumerate(raft_ccds):

            image_file = glob(join(image_dir, raft_ccd, '*_{0:03d}.fits'.format(pos)))[0]
            ccd_array = fits.open(image_file)

            for amp in range(1, 17):            
                raft_array[ccd*16+amp-1,:,:] = ccd_array[amp].data[ylow:yhigh, xlow:xhigh]

            logger.info("CCD {0} added.".format(raft_ccd))
            ccd_array.close()

        ## Loop over each amp to find the 4 aggressor spots
        agg_count = 0
        agg_amp = 0
        while agg_count < num_aggressors_per_position:

            try:
                aggressor = raft_array[agg_amp, :, :]
            except IndexError as err:
                err.message = err.message + " Failed to find all aggressors in an image."
                raise

            ## Verify that aggressor spot is present
            try:
                ay, ax = find_spot(aggressor, sigma)
            except TypeError:
                agg_amp += 1
                continue
            else:
                agg_count += 1

            agg_amp_pos = get_amp_pos(agg_amp)
            logger.info("Aggressor found at {0}, amplifier {1}".format(*agg_amp_pos))
            print("Aggressor found at {0}, amplifier {1}".format(*agg_amp_pos))
            lookup_dict[agg_amp] = (pos, agg_amp_pos[0], agg_amp_pos[1])
            aggressor_stamp = stamp(aggressor, ay, ax, length)

            ## Loop over each amp to measure xtalk
            for vic_amp in range(144):

                if agg_amp == vic_amp:
                    xtalk_array[agg_amp, vic_amp] = 1.0
                    continue

                victim = raft_array[vic_amp, :, :]
                victim_stamp = stamp(victim, ay, ax, length)

                ## Mask invalid entries first
                results = np.asarray([[0,0,0,0]])
                masked_victim_stamp = np.ma.masked_invalid(victim_stamp)
                mask = np.ma.getmask(masked_victim_stamp)

                for i in range(num_iterations):

                    ## Calculate residual
                    model = victim_model(results[0], aggressor_stamp)
                    masked_model = np.ma.masked_where(mask, model)
                    res = masked_victim_stamp - masked_model
                    res_mean = np.mean(res)
                    res_std = np.std(res)

                    ## Mask 3 sigma outliers
                    masked_victim_stamp = np.ma.masked_where(np.abs(res-res_mean) > 2.0*res_std, 
                                                             victim_stamp)
                    mask = np.ma.getmask(masked_victim_stamp)
                    victim_std = np.std(masked_victim_stamp)

                    ## Construct masked basis arrays
                    background = np.ones(aggressor_stamp.shape)
                    Y, X = np.mgrid[:aggressor_stamp.shape[0], :aggressor_stamp.shape[1]]

                    masked_aggressor_stamp = np.ma.masked_where(mask, aggressor_stamp)
                    masked_background = np.ma.masked_where(mask, background)
                    masked_Y = np.ma.masked_where(mask, Y)
                    masked_X = np.ma.masked_where(mask, X)

                    ## Perform least-square minimization
                    b = masked_victim_stamp.compressed()/victim_std
                    A = np.vstack([masked_aggressor_stamp.compressed(), 
                                   masked_background.compressed(),
                                   masked_Y.compressed(), masked_X.compressed()]).T/victim_std

                    results = np.linalg.lstsq(A, b)
                    covar = np.matrix(np.dot(A.T, A)).I

                xtalk_array[agg_amp, vic_amp] = results[0][0]
                background_array[agg_amp, vic_amp] = results[0][1]
                tilty_array[agg_amp, vic_amp] = results[0][2]
                tiltx_array[agg_amp, vic_amp] = results[0][3]                    
                error_array[agg_amp, vic_amp] = np.sqrt(np.abs(covar[0, 0]))

            agg_amp += 1
                        
    ## Save results and look-up table to file
    xtalk_hdu = fits.PrimaryHDU(xtalk_array)    
    background_hdu = fits.ImageHDU(background_array, name='BIAS')
    tilty_hdu = fits.ImageHDU(tilty_array, name='TILT_Y')
    tiltx_hdu = fits.ImageHDU(tiltx_array, name='TILT_X')
    error_hdu = fits.ImageHDU(error_array, name='XTALK_ERROR')

    hdu_list = fits.HDUList([xtalk_hdu, background_hdu, tilty_hdu, tiltx_hdu, error_hdu])
    hdu_list.writeto(join(image_dir, 'xtalk_results.fits'), overwrite=True)

    np.save(join(image_dir, 'xtalk_lookup_table.npy'), lookup_dict)
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', 
                        help='Main directory containing calibrated xtalk images.')
    parser.add_argument('-l', '--length', type=int, default=200, 
                        help='Side length of square postage stamp.')
    parser.add_argument('-s', '--smoothing', type=int, default=50,
                        help='Pixel smoothing scale.')
    parser.add_argument('-p', '--positions', type=int, default=36,
                        help='Number of xtalk positions.')
    parser.add_argument('-a', '--aggressors', type=int, default=4,
                        help='Number of aggressor spots per xtalk position.')
    parser.add_argument('-i', '--iterations', type=int, default=5,
                        help='Number of minimization iterations per xtalk model fit.')
    args = parser.parse_args()

    imdir = args.directory
    length = args.length
    smoothing = args.smoothing
    num_positions = args.positions
    num_aggressors_per_position = args.aggressors
    num_iterations = args.iterations

    main(imdir, length, smoothing, num_positions, num_aggressors_per_position, num_iterations)
