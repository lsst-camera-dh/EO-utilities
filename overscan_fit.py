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
        
        self.meanrow_data = dict((amp, []) for amp in range(1, 17))
        self.flux = dict((amp, []) for amp in range(1, 17))
        self.flux_var = dict((amp, []) for amp in range(1, 17))
        self.exp = dict((amp, []) for amp in range(1, 17))
        self.exp_var = dict((amp, []) for amp in range(1, 17))
        self.tau = dict((amp, []) for amp in range(1, 17))
        self.tau_var = dict((amp, []) for amp in range(1, 17))
        self.cti = dict((amp, []) for amp in range(1, 17))
        self.cti_var = dict((amp, []) for amp in range(1, 17))

    def process_image(self, ccd, amp, gains):

        image = ccd.bias_subtracted_image(amp) # bias/overscan kwargs

        ## get xmin, xmax, ymin, ymax here
        amp_geom = parse_geom_kwd(ccd.amp_geom[1]['DATASEC'])
        xmin = amp_geom['xmin']
        xmax = amp_geom['xmax']
        ymin = amp_geom['ymin']
        ymax = amp_geom['ymax']

        imarr = image.getImage().getArray()
        meanrow_data = np.mean(imarr[ymin-1:ymax, :], axis=0)*gains[amp]
        flux = np.mean(imarr[ymin-1:ymax, xmin-1:xmax]*gains[amp])
        flux_var = np.var(imarr[ymin-1:ymax, xmin-1:xmax]*gains[amp])
        exp = np.nan
        tau = np.nan
        cti = np.nan
        exp_var = np.nan
        tau_var = np.nan
        cti_var = np.nan
        
        if self.minflux <= flux <= self.maxflux:
            y = copy.deepcopy(meanrow_data[xmax:xmax+self.num_pixels])
            x = np.arange(1, y.shape[0]+1)

            try:
                fit_params, fit_covar = curve_fit(make_joint_model(flux, xmax),
                                                  x, y, p0=(50, 1.25, 1E-6))
            except RuntimeError:
                print("Error for fit: flux = {0:.1f}, Skipping...".format(flux))
            else:
                exp = fit_params[0]
                tau = fit_params[1]
                cti = fit_params[2]
                exp_var = fit_covar[0, 0]
                tau_var = fit_covar[1, 1]
                cti_var = fit_covar[2, 2]
            
        self._save_ext_data(amp, flux, flux_var, exp, exp_var, tau, tau_var,
                            cti, cti_var, np.array(meanrow_data))
                
        self.flux[amp].append(flux)
        self.exp[amp].append(exp)
        self.tau[amp].append(tau)
        self.cti[amp].append(cti)
        self.flux_var[amp].append(flux_var)
        self.exp_var[amp].append(exp_var)
        self.tau_var[amp].append(tau_var)
        self.cti_var[amp].append(cti_var)
        self.meanrow_data[amp].append(meanrow_data)

    def _save_ext_data(self, amp, flux, flux_var, exp, exp_var, tau, tau_var,
                       cti, cti_var, meanrow_data):
        """
        Write results from the overscan fit to to the FITS extension 
        corresponding to the specified amplifier.
        """
        extname = 'Amp{0:02d}'.format(amp)
        try:
            #
            # Append new rows if HDU for this segment already exists.
            #
            table_hdu = self.output[extname]
            row0 = table_hdu.header['NAXIS2']
            nrows = row0 + 1
            table_hdu = fitsTableFactory(table_hdu.data, nrows=nrows)
            table_hdu.data[row0]['FLUX'] = flux
            table_hdu.data[row0]['FLUX_VAR'] = flux_var
            table_hdu.data[row0]['EXP'] = exp
            table_hdu.data[row0]['EXP_VAR'] = exp_var
            table_hdu.data[row0]['TAU'] = tau
            table_hdu.data[row0]['TAU_VAR'] = tau_var
            table_hdu.data[row0]['CTI'] = cti
            table_hdu.data[row0]['CTI_VAR'] = cti_var
            table_hdu.data[row0]['MEANROW_DATA'] = meanrow_data
            table_hdu.name = extname
            self.output[extname] = table_hdu
        except KeyError:
            #
            # Extension for this segment does not yet exist, so add it.
            #
            colnames = ['FLUX', 'FLUX_VAR', 'EXP', 'EXP_VAR', 'TAU', 'TAU_VAR',
                        'CTI', 'CTI_VAR', 'MEANROW_DATA']
            columns = [np.array([flux]), np.array([flux_var]),
                       np.array([exp]), np.array([exp_var]),
                       np.array([tau]), np.array([tau_var]),
                       np.array([cti]), np.array([cti_var]),
                       np.array([meanrow_data])]
            formats = ['E']*(len(columns)-1) + ['{0}E'.format(len(meanrow_data))]
            units = ['electrons', 'electrons^2', 'electrons', 'electrons^2',
                     'None', 'None', 'None', 'None', 'electrons']
            fits_cols = lambda coldata: [fits.Column(name=colname,
                                                     unit=unit,
                                                     format=format,
                                                     array=column)
                                         for colname, format, unit, column
                                         in coldata]
            self.output.append(fitsTableFactory(fits_cols(zip(colnames,
                                                              formats,
                                                              units,
                                                              columns))))
            self.output[-1].name = extname

    def write_results(self, outfile='overscan_fit_params.fits'):
        self.output[0].header['NAMPS'] = 16
        fitsWriteto(self.output, outfile, overwrite=True, checksum=True)
