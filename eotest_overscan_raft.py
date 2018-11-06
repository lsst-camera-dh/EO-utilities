"""
@brief Additional analysis on flat pair eotest
"""
import glob
import argparse
import astropy.io.fits as fits
from os.path import join

from overscanTask import OverscanTask

def main(directory, output_dir):

    ccd_names = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']

    for sensor_id in ccd_names:

        ## Get flat and bias images
        flat_pair_dir = join(directory, 'flat_pair_raft_acq', 
                             'v0', '*', sensor_id)                         
        flat1_files = sorted(glob.glob(join(flat_pair_dir, '*flat1*.fits')))
        bias_files = sorted(glob.glob(join(flat_pair_dir, '*flat_bias*.fits')))
        
        ## Get amplifier gains
        with fits.open(flat1_files[0]) as hdulist:
            lsst_num = hdulist[0].header['LSST_NUM']          
        results = glob.glob(join(directory, 'collect_raft_results', 
                                 'v0', '*', 
                                 '{0}_eotest_results.fits'.format(lsst_num)))[0]
        with fits.open(results) as hdulist:
            gains_array = hdulist[1].data['GAIN']
            gains = dict((i+1, gains_array[i]) for i in range(16))

        ## Run overscan task
        overscantask = OverscanTask()
        overscantask.config.output_dir = output_dir
        overscantask.run(sensor_id, flat1_files, gains, bias_frame=bias_files[0])

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

