"""
Ultraflats task for EOTest code.
"""

from os.path import join 
import glob
import numpy as np
import scipy.optimize
import astropy.io.fits as fits
from lsst.eotest.fitsTools import fitsTableFactory, fitsWriteto
import lsst.eotest.image_utils as imutils
from lsst.eotest.sensor.MaskedCCD import MaskedCCD
from lsst.eotest.sensor.EOTestResults import EOTestResults
from lsst.eotest.sensor.AmplifierGeometry import makeAmplifierGeometry

from scipy import ndimage, stats
import sys

import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase


def glob_flats(full_path, outfile = 'single_pixel_ptc.txt'):
	flats = glob.glob(join(full_path, '20*.fits'))
	output = open(outfile, 'w')
	for item in flats:
		output.write('%s\n' % item)
	output.close()

class UltraflatStackStats(object):
	def __init__(self, fmean, fvar):
		self.flats_mean = fmean 
		self.flats_var = fvar
		self.flats_med = fmed

class PtcConfig(pexConfig.Config):
	"""Configuration for ptc task"""
	output_dir = pexConfig.Field("Output directory", str, default='.')
	eotest_results_file = pexConfig.Field("EO test results filename", str, default=
None)
	max_frac_offset = pexConfig.Field("maximum fraction offset from median gain curve to omit points from PTC fit.", float, default=0.2)
	verbose = pexConfig.Field("Turn verbosity on", bool, default=True)

class UltraFlatsTask(pipeBase.Task):
	"""Task to compute a variety of statistics on ultraflats dataset."""
	ConfigClass = PtcConfig
	_DefaultName = "UltraflatsTask"
	
	@pipeBase.timeMethod
	def stack(self, sensor_id, infiles, mask_files, gains, binsize=1, bias_frame = None,exps=['0.27','0.54','1.60','2.40']):
		exps = ['0.27','1.60','2.40']
		for exp in exps:
        		in_file_path = '/nfs/slac/g/ki/ki19/lsst/elp25/S11'
			files = glob.glob(join(in_file_path, '20*'+exp+'*.fits'))
        		bias_frame = glob.glob(join(in_file_path, '*bias*'))[0]
			#'ITL-3800C-090_sflat_bias_000_4663_20170621212349.fits'
			#outfile = os.path.join(self.config.output_dir, '%s_ptc.fits' % sensor_id)
			all_amps = imutils.allAmps(infiles[0])
			#ptc_stats = dict([amp, ([],[])) for amp in all_amps])
			exposure = []	
			bitpix = None
			overscan = makeAmplifierGeometry(files[0]).serial_overscan

			mean_stack = fits.open(files[0])
			var_stack = fits.open(files[0])
			sum_stack = fits.open(files[0])
			median_stack = fits.open(files[0])
			for amp in imutils.allAmps(files[0]):
				images = afwImage.vectorImageF()
				for idx, infile in enumerate(files):
					ccd = MaskedCCD(infile, mask_files = (), bias_frame = bias_frame)
					image = ccd.unbiased_and_trimmed_image(amp)

					if idx == 0:
						fratio_im = afwImage.MaskedImageF(image)
						fratio_im = fratio_im.getImage().getArray()
					image_array = image.getImage().getArray()
					fratio = np.mean(fratio_im[50:fratio_im.shape[0]-50,50:fratio_im.shape[1]-50])/np.mean(image_array[50:image_array.shape[0]-50,50:image_array.shape[1]-50])
					image = afwImage.MaskedImageF(image).getImage()
                        		image *= fratio
                        		images.push_back(image)

					meanstack_image = afwMath.statisticsStack(images, afwMath.MEAN)
					varstack_image = afwMath.statisticsStack(images, afwMath.VARIANCE)
					sumstack_image = afwMath.statisticsStack(images, afwMath.SUM)
					medianstack_image = afwMath.statisticsStack(images, afwMath.MEDIAN)
					
					mean_stack[amp].data = meanstack_image.getArray()
					var_stack[amp].data = varstack_image.getArray()

					sum_stack[amp].data = sumstack_image.getArray()
					median_stack[amp].data = medianstack_image.getArray()


                        		if bitpix is not None:
                                		imutils.set_bitpix(output[amp], bitpix)

			fitsWriteto(mean_stack, sensor_id + '_mean_image_'+exp+'.fits',clobber = True)
			fitsWriteto(var_stack, sensor_id + '_var_image_'+exp+'.fits', clobber = True)
			fitsWriteto(sum_stack, sensor_id +'_sum_image_'+exp+'.fits', clobber = True)
			fitsWriteto(median_stack, sensor_id +'_median_image_'+exp+'.fits', clobber = True)
			
	def single_pixel_ptc(self,meanimages,varimages,infiles):
		gain_map = fits.open(infiles[0])
		for amp in imutils.allAmps(infiles[0]):
			meanmaps =  [afwImage.ImageF(meanimage).getArray() for meanimage in meanimages]
			varmaps = [afwImage.ImageF(varimage).getArray() for varimage in varimages]
			gain_map = np.zeros((meanmaps[0].shape[0],meanmaps[0].shape[1]))
			for x in range(meanmaps[0].shape[0]):
				for y in range(meanmaps[0].shape[1]):
					means = [meanmap[x][y] for meanmap in meanmaps]
					varrs = [varmap[x][y] for varmap in varmaps]
					print means
					print varrs
					slope, intercept, r_value, p_value, std_err = stats.linregress(means,varrs)
					gain_map[x][y] = 1/slope
        	print np.median(gain_map)
        	ptc = np.median(gain_map)
        	
        	# Write a fits file of the gain map 
        	
        	
        	 # Write gain and error to EO test results file.
            output.add_seg_result(amp, 'SINGLE_PIXEL_PTC_GAIN', ptc_gain)
            output.add_seg_result(amp, 'SINGLE_PIXEL_PTC_GAIN_ERROR', ptc_error)
            self.log.info("%i  %f  %f" % (amp, ptc_gain, ptc_error))
        output.write()
        fitsWriteto(mean_stack, 'gain_map_.fits',clobber = True)
			
        	
		


