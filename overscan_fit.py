"""
@brief Fit exponential model to mean serial overscans.

@author A. Snyder <snyder18@stanford.edu>
"""
from __future__ import print_function
from __future__ import absolute_import

import numpy as np
import copy
from astropy.io import fits
from scipy.optimize import curve_fit

from lsst.eotest.fitsTools import fitsWriteto, fitsTableFactory
from lsst.eotest.sensor import MaskedCCD, parse_geom_kwd

def make_joint_model(flux, N):
    """Make high flux exponential plus CTI model."""
    
    def joint_model(x, A, tau, cti):
        
        result = A*np.exp(-x/tau) + (cti**x)*N*flux
        
        return result
        
    return joint_model

class OverscanFit(object):

    def __init__(self, num_pixels=10, minflux=30000., maxflux=150000., 
                 outfile=None):

        self.num_pixels = num_pixels
        if maxflux <= minflux:
            raise ValueError("maxflux must be greater than minflux")
        self.minflux = minflux
        self.maxflux = maxflux
        self.outfile = outfile
        if outfile is None:
            self.output = fits.HDUList()
            self.output.append(fits.PrimaryHDU())
        else:
            self.output = fits.open(self.outfile)

        self.meanrow = {i : [] for i in range(1, 17)}
        self.noise = {i : [] for i in range(1, 17)}
        self.flux = {i : [] for i in range(1, 17)}
        self.flux_std = {i : [] for i in range(1, 17)}
        self.amp = {i : [] for i in range(1, 17)}
        self.amp_std = {i : [] for i in range(1, 17)}
        self.tau = {i : [] for i in range(1, 17)}
        self.tau_std = {i : [] for i in range(1, 17)}
        self.cti = {i : [] for i in range(1, 17)}
        self.cti_std = {i : [] for i in range(1, 17)}

    def process_image(self, ccd, i, gains):

        image = ccd.bias_subtracted_image(i)

        ## get xmin, xmax, ymin, ymax here
        amp_geom = parse_geom_kwd(ccd.amp_geom[1]['DATASEC'])
        xmin = amp_geom['xmin']
        xmax = amp_geom['xmax']
        ymin = amp_geom['ymin']
        ymax = amp_geom['ymax']

        imarr = image.getImage().getArray()*gains[i]

        meanrow = np.mean(imarr[ymin-1:ymax, :], axis=0)
        noise = np.std(imarr[ymin-1:ymax, xmax+2:xmax+28])
        flux = np.mean(imarr[ymin-1:ymax, xmin-1:xmax])
        flux_std = np.std(imarr[ymin-1:ymax, xmin-1:xmax])
        amp = np.nan
        tau = np.nan
        cti = np.nan
        amp_std = np.nan
        tau_std = np.nan
        cti_std = np.nan
        
        if self.minflux <= flux <= self.maxflux:
            y = copy.deepcopy(meanrow[xmax:xmax+self.num_pixels])
            x = np.arange(1, y.shape[0]+1)

            try:
                fit_params, fit_covar = curve_fit(make_joint_model(flux, xmax),
                                                  x, y, p0=(50, 1.25, 1E-6))
            except RuntimeError:
                print("Error for fit: flux = {0:.1f}, Skipping...".format(flux))
            else:
                amp = fit_params[0]
                tau = fit_params[1]
                cti = fit_params[2]
                amp_std = np.sqrt(fit_covar[0, 0])
                tau_std = np.sqrt(fit_covar[1, 1])
                cti_std = np.sqrt(fit_covar[2, 2])
                
        self.meanrow[i].append(meanrow)
        self.flux[i].append(flux)
        self.flux_std[i].append(flux_std)
        self.noise[i].append(noise)
        self.amp[i].append(amp)
        self.tau[i].append(tau)
        self.cti[i].append(cti)
        self.amp_std[i].append(amp_std)
        self.tau_std[i].append(tau_std)
        self.cti_std[i].append(cti_std)

    def write_results(self, outfile):
        
        for i in range(1, 17):
            extname = 'Amp{0:02d}'.format(i)
            nrows1 = len(self.flux[i])

            meanrow_col = fits.Column('MEANROW_DATA', format='{0}E'.format(len(self.meanrow[i][0])),
                                      unit='e-', array=self.meanrow[i])
            flux_col = fits.Column('FLUX', format='E', unit='e-', array=self.flux[i])
            flux_std_col = fits.Column('FLUX_STD', format='E', unit='e-', array=self.flux_std[i])
            noise_col = fits.Column('NOISE', format='E', unit='e-', array=self.noise[i])
            amp_col = fits.Column('MODEL_AMP', format='E', unit='e-', array=self.amp[i])
            amp_std_col = fits.Column('MODEL_AMP_STD', format='E', unit='e-', array=self.amp_std[i])
            tau_col = fits.Column('MODEL_TAU', format='E', unit='None', array=self.tau[i])
            tau_std_col = fits.Column('MODEL_TAU_STD', format='E', unit='None', array=self.tau_std[i])
            cti_col = fits.Column('MODEL_CTI', format='E', unit='None', array=self.cti[i])
            cti_std_col = fits.Column('MODEL_CTI_STD', format='E', unit='None', array=self.cti_std[i])

            try:
                #
                # Append new rows if HDU for this segment already exists
                #
                table_hdu = self.output[extname]
                row0 = table_hdu.header['NAXIS2']
                nrows = row0+nrows1
                table_hdu = fitsTableFactory(table_hdu.data, nrows=nrows)
                table_hdu.data['MEANROW_DATA'][row0:] = meanrow_col
                table_hdu.data['FLUX'][row0:] = flux_col
                table_hdu.data['FLUX_STD'][row0:] = flux_std_col
                table_hdu.data['NOISE'][row0:] = noise_col
                table_hdu.data['MODEL_AMP'][row0:] = amp_col
                table_hdu.data['MODEL_AMP_STD'][row0:] = amp_std_col
                table_hdu.data['MODEL_TAU'][row0:] = tau_col
                table_hdu.data['MODEL_TAU_STD'][row0:] = tau_std_col
                table_hdu.data['MODEL_CTI'][row0:] = cti_col
                table_hdu.data['MODEL_CTI_STD'][row0:] = cti_std_col
                table_hdu.name = extname
                self.output[extname] = table_hdu
            except KeyError:
                self.output.append(fitsTableFactory([meanrow_col, 
                                                     flux_col,
                                                     flux_std_col,
                                                     noise_col,
                                                     amp_col,
                                                     amp_std_col,
                                                     tau_col,
                                                     tau_std_col,
                                                     cti_col,
                                                     cti_std_col]))
                self.output[-1].name = extname

        self.output[0].header['NAMPS'] = 16
        fitsWriteto(self.output, outfile, overwrite=True, checksum=True)
