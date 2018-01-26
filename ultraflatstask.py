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


def glob_flats(full_path, outfile = 'ultraflats.txt'):
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
		for exp in exps:
        		
			all_amps = imutils.allAmps(infiles[0])
			#ptc_stats = dict([amp, ([],[])) for amp in all_amps])
			exposure = []	
			bitpix = None
			overscan = makeAmplifierGeometry(infiles[0]).serial_overscan

			mean_stack = fits.open(infiles[0])
			var_stack = fits.open(infiles[0])
			sum_stack = fits.open(infiles[0])
			median_stack = fits.open(infiles[0])
			for amp in imutils.allAmps(infiles[0]):
				print 'on amp number', amp
				images = afwImage.vectorImageF()
				for idx, infile in enumerate(infiles):
					print infile
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

			fitsWriteto(mean_stack, 'mean_image_'+exp+'.fits',clobber = True)
			fitsWriteto(var_stack, 'var_image_'+exp+'.fits', clobber = True)
			fitsWriteto(sum_stack, 'sum_image_'+exp+'.fits', clobber = True)
			fitsWriteto(median_stack, 'median_image_'+exp+'.fits', clobber = True)
			
	def single_pixel_ptc(self,meanimages,varimages,infiles):
		gain_map_image = fits.open(infiles[0])
		for amp in imutils.allAmps(infiles[0]):
			meanmaps =  [afwImage.ImageF(meanimage).getArray() for meanimage in meanimages]
			varmaps = [afwImage.ImageF(varimage).getArray() for varimage in varimages]
			gain_map = np.zeros((meanmaps[0].shape[0],meanmaps[0].shape[1]))
			for x in range(meanmaps[0].shape[0]):
				for y in range(meanmaps[0].shape[1]):
					means = [meanmap[x][y] for meanmap in meanmaps]
					varrs = [varmap[x][y] for varmap in varmaps]
					slope, intercept, r_value, p_value, std_err = stats.linregress(means,varrs)
					gain_map[x][y] = 1/slope
			gain_map_image[amp].data = gain_map
        	print np.median(gain_map)
        fitsWriteto(gain_map_image, 'gain_map.fits',clobber=True)
			
        	
		


