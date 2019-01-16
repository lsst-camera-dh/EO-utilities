import argparse
import os
import errno
from astropy.io import fits
import configparser

from exploreRaft import exploreRaft
from findCCD import findCCD
from deferredChargePlots import *
from overscanTask import OverscanTask
from lsst.eotest.sensor import parse_geom_kwd
import lsst.eotest.image_utils as imutils

def main(rtm_id, output_dir='./', db='Prod', mirrorName='vendor'):
    
    raftName = 'LCA-11021_RTM-{0}'.format(rtm_id)

    ## Get CCD names
    eR = exploreRaft(db)
    sensor_list = eR.raftContents(raftName)

    ## Make output directory if doesn't exist
    try:
        os.makedirs(output_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    ## Iterate over sensors in raft
    for sensor_info in sensor_list[:1]:
        print(sensor_info)

        ## Set up output directory
        sensor_name = sensor_info[0]
        sensor_pos = sensor_info[1]
        ccd_output_dir = os.path.join(output_dir, sensor_pos)
        try:
            os.makedirs(ccd_output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        ## Get vendor PTC data
        fCCD = findCCD(mirrorName=mirrorName, 
                       sensorId=sensor_name, 
                       db=db, prodServer='Dev', 
                       appSuffix='-jrb')
        imfiles = fCCD.find(FType='fits')
        flat_files = [f for f in imfiles if 'ptc' in f]
        bias_files = [f for f in imfiles if 'superbias' in f]

        ## Make superbias file
        try:
            print("Making superbias")
            amp_geom = makeAmplifierGeometry(bias_files[0])
            overscan = amp_geom.serial_overscan
            sbias = os.path.join(ccd_output_dir, '{0}_superbias.fits'.format(sensor_pos))
            super_bias_file(bias_files, overscan, sbias)
        except Exception as e:  
            print(e)
            print("Sbias failed, using first bias instead")
            sbias = bias_files[0]

        ## Get vendor gains results from txt file
        txt_files = fCCD.find(FType='txt')
        gain_file = [f for f in txt_files if 'gain' in f][0]

        config = configparser.ConfigParser()
        config.read(gain_file)
        g = config['SystemGain']
        gains = dict((i+1, float(g['Gain_{0:02d}'.format(i)])) for i in range(16))

        ## Run overscan task
        ccd_output_dir = os.path.join(output_dir, sensor_pos)
        try:
            os.makedirs(ccd_output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        overscantask = OverscanTask()
        overscantask.config.output_dir = ccd_output_dir
        output_file = overscantask.run(sensor_pos, flat_files, gains, 
                                       bias_frame=sbias)

        # modify below to be in the results header already
        with fits.open(flat_files[0]) as hdulist:
            datasec = parse_geom_kwd(hdulist[1].header['DATASEC'])
            xmax = datasec['xmax']

        eper_plot(sensor_pos, output_file, xmax=xmax, 
                  output_dir=ccd_output_dir)
        first_overscan_plot(sensor_pos, output_file, xmax=xmax, 
                            output_dir=ccd_output_dir)
        second_overscan_plot(sensor_pos, output_file, xmax=xmax, 
                             output_dir=ccd_output_dir)
        cti_plot(sensor_pos, output_file, xmax=xmax, 
                 output_dir=ccd_output_dir)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('rtm_id', type=str,
                        help='RTM number (e.g. 004, 005, etc.)')
    parser.add_argument('-o', '--output_dir', type=str, default='./',
                        help='Output directory for analysis results.')
    parser.add_argument('-d', '--db', default='Prod',
                        help='eT database (Prod, Dev)')
    parser.add_argument('-m', '--mirrorName', default='vendor',
                        help='mirror name to search')
    args = parser.parse_args()
    
    rtm_id = args.rtm_id
    db = args.db
    mirrorName = args.mirrorName
    output_dir=args.output_dir

    main(rtm_id, output_dir=output_dir, db=db, mirrorName=mirrorName)

