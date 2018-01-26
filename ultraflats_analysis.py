import glob
import argparse
#import lsst.eotest.sensor as sensorTest
from ultraflatstask import UltraFlatsTask
from os.path import join 


sensor_id = 'ITL-3800c-090'
in_file_path = '/nfs/slac/g/ki/ki19/lsst/elp25/S11/ultratask/'
infiles = glob.glob(join(in_file_path, '00*.fits'))
#bias = glob.glob(join(in_file_path, '*bias*.fits'))[0]
bias = 'ITL-3800C-090_sflat_bias_000_4663_20170621212349.fits'
mask_files = ()
gains = 1

ultratask = UltraFlatsTask()
ultratask.config.output_dir = '/nfs/slac/g/ki/ki19/lsst/elp25/S11/ultratask/'
ultratask.stack(sensor_id=sensor_id, infiles=infiles, mask_files=mask_files, gains=gains, binsize=1, bias_frame = bias)


in_file_path = '/nfs/slac/g/ki/ki19/lsst/elp25/S11/ultratask/'
ultratask = UltraFlatsTask()
infiles = glob.glob(join('/nfs/slac/g/ki/ki19/lsst/elp25/S11/ultratask/', '00*.fits'))
meanimages = glob.glob(join(in_file_path, 'mean*.fits'))
varimages = glob.glob(join(in_file_path, 'var*.fits'))
ultratask.single_pixel_ptc(meanimages, varimages,infiles)



