"""
@brief Additional overscan analysis on flat pair eotest
"""
from __future__ import print_function
from __future__ import absolute_import
import os
import numpy as np
import astropy.io.fits as fits

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.eotest.image_utils as imutils
from lsst.eotest.fitsTools import fitsWriteto
from lsst.eotest.sensor import MaskedCCD, parse_geom_kwd

class OverscanConfig(pexConfig.Config):
    """Configuration for overscan analysis task"""
    output_dir = pexConfig.Field("Output directory", str, default='.')
    output_file = pexConfig.Field("Output filename", str, default=None)
    smoothing = pexConfig.Field("Smoothing for spline overscan correction",
                                int, default=11000)
    verbose = pexConfig.Field("Turn verbosity on", bool, default=True)

class OverscanTask(pipeBase.Task):
    """Task to calculate mean row results from flat pair dataset."""
    ConfigClass = OverscanConfig
    _DefaultName = "OverscanTask"

    def run(self, sensor_id, infiles, gains, bias_frame=None):

        with fits.open(infiles[0]) as hdulist:
            datasec = parse_geom_kwd(hdulist[1].header['DATASEC'])
            ymin = datasec['ymin']
            ymax = datasec['ymax']
            xmin = datasec['xmin']
            xmax = datasec['xmax']
            ny, nx = hdulist[1].shape

        ## Calculate mean row for each flat file
        results = np.zeros((16, len(infiles), nx))
        for i, infile in enumerate(infiles):
            if self.config.verbose:
                self.log.info("Processing {0}".format(infile))
            ccd = MaskedCCD(infile, bias_frame=bias_frame)
            for amp in range(1, 17):
                smoothing = self.config.smoothing
                image = ccd.bias_subtracted_image(amp, s=smoothing)
                imarr = image.getImage().getArray()
                results[amp-1, i, :] = np.mean(imarr[ymin-1:ymax, :],
                                               axis=0)*gains[amp]

        ## Sort results array by increasing flux
        flux = np.median(results[:, :, xmin-1:xmax], axis=(0, 2))
        indices = np.argsort(flux)
        results = results[:, indices, :]
        
        ## Save as FITs file
        hdu = fits.PrimaryHDU(results)
        hdul = fits.HDUList([hdu])
        output_dir = self.config.output_dir
        if self.config.output_file is None:
            output_file = os.path.join(output_dir, 
                                       '{0}_mean_rows_results.fits'.format(sensor_id))
        else:
            output_file = os.path.join(output_dir, self.config.output_file)
        if self.config.verbose:
            self.log.info("writing to {0}".format(output_file))
        fitsWriteto(hdul, output_file, overwrite=True)

        return output_file
