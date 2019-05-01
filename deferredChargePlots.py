"""
@brief Analysis plots for studying deferred charge
"""
import os
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
import argparse

def eper_plot(sensor_id, results_file, xmax=512, output_dir='./'):
    """Plot of overscans as a function of flux."""

    ## Set-up figure
    fig, axes = plt.subplots(4, 4, sharey=True, sharex=True, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)
    axes = axes.flatten()
    
    hdulist = fits.open(results_file)
    
    ## Create and save overscan vs flux graphs
    target_flux_levels = [100, 1000, 10000, 25000, 50000, 75000, 100000]
    for i in range(16):
        
        target_flux_index = 0
        data = hdulist[i+1].data        
        sorted_indices = np.argsort(data['FLUX'])
                
        for row in sorted_indices:
            
            flux = data['FLUX'][row]
            
            if flux > target_flux_levels[target_flux_index]:
                
                meanrow = data['MEANROW'][row, :]
                offset = np.mean(meanrow[-20:])
                overscan = meanrow[xmax:] - offset
                columns = np.arange(xmax, meanrow.shape[0])
        
                axes[i].plot(columns, overscan, label='{0:d} e-'.format(int(round(flux, -2))))
                axes[i].set_yscale('symlog', linthreshy=1.0)
                axes[i].set_ylim(-2, 300)
                axes[i].set_yticklabels([r'$-1$', '0', '1', r'$10^{1}$', r'$10^{2}$'])
                axes[i].grid(True, which='major', axis='both')
                axes[i].set_title('Amp {0}'.format(i+1), fontsize=10)
                axes[i].tick_params(axis='both', which='minor')
                if i >= 12: axes[i].set_xlabel('Overscan Pixel Number')
                if i % 4 == 0: axes[i].set_ylabel('Signal [e-]')
                    
                target_flux_index += 1
                if target_flux_index == len(target_flux_levels): break
                        
    h, l = axes[-1].get_legend_handles_labels()
    fig.subplots_adjust(bottom=0.13)
    fig.legend(h, l, loc='lower center', ncol=len(target_flux_levels))
    plt.suptitle('{0} Mean Overscans'.format(sensor_id))
    plt.savefig(os.path.join(output_dir, 
                             '{0}_mean_overscan.png'.format(sensor_id)))
    plt.close()
    hdulist.close()

def overscan1_plot(sensor_id, results_file, xmax=512, maxflux=150000., 
                        output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)
    
    hdulist = fits.open(results_file)
    
    for i in range(16):
        
        if i >= 10: marker = 's'
        else: marker = '^'
            
        data = hdulist[i+1].data        
        sorted_indices = np.argsort(data['FLUX'])
        
        offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)        
        overscan1 = data['MEANROW'][sorted_indices, xmax] - offset
        flux = data['FLUX'][sorted_indices] - offset
        
        ax.plot(flux[flux <= maxflux], overscan1[flux <= maxflux], 
                  label="Amp {0}".format(i+1), marker=marker)
        
    ax.set_yscale('symlog', threshold=1.0)
    ax.set_xscale('log')
    ax.set_ylim(bottom=-1.0)
    ax.set_xlim(left=50)
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('First Overscan [e-]', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper left', ncol=4, fontsize=12)
    ax.set_title('First Overscan vs. Flux', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_first_overscan.png'.format(sensor_id)))
    plt.close()
    hdulist.close()

def overscan2_plot(sensor_id, results_file, xmax=512, maxflux=150000., output_dir='./'):
    """Plot of the second overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)
    
    hdulist = fits.open(results_file)
    
    for i in range(16):
        
        if i >= 10: marker = 's'
        else: marker = '^'
            
        data = hdulist[i+1].data        
        sorted_indices = np.argsort(data['FLUX'])
        
        offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)        
        overscan2 = data['MEANROW'][sorted_indices, xmax+1] - offset
        flux = data['FLUX'][sorted_indices] - offset
        
        ax.plot(flux[flux <= maxflux], overscan2[flux <= maxflux], 
                  label="Amp {0}".format(i+1), marker=marker)
        
    ax.set_yscale('symlog', threshold=1.0)
    ax.set_xscale('log')
    ax.set_ylim(bottom=-1.0)
    ax.set_xlim(left=50)
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('Second Overscan [e-]', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper left', ncol=4, fontsize=12)
    ax.set_title('Second Overscan vs. Flux', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_second_overscan.png'.format(sensor_id)))
    plt.close()
    hdulist.close()

def summedoverscan_plot(sensor_id, results_file, xmax=512, maxflux=150000., 
                        output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)
    
    hdulist = fits.open(results_file)
    
    for i in range(16):
        
        if i >= 10: marker = 's'
        else: marker = '^'
            
        data = hdulist[i+1].data        
        sorted_indices = np.argsort(data['FLUX'])
        
        offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)        
        summedoverscan = np.sum(data['MEANROW'][sorted_indices, xmax+8:xmax+18], axis=1) - offset
        flux = data['FLUX'][sorted_indices] - offset
        
        ax.plot(flux[flux <= maxflux], summedoverscan[flux <= maxflux], 
                  label="Amp {0}".format(i+1), marker=marker)
        
    ax.set_xscale('log')
    ax.set_ylim(-2.0)
    ax.set_xlim(left=50)
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('Summed Overscan [e-]', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper left', ncol=4, fontsize=12)
    ax.set_title('Summed Overscan[8:18] vs. Flux', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_summed_overscan.png'.format(sensor_id)))
    plt.close()
    hdulist.close()

def cti_plot(sensor_id, results_file, xmax=512, maxflux=150000., output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)

    hdulist = fits.open(results_file)

    for i in range(16):

        if i >= 10: marker = 's'
        else: marker = '^'
            
            
        data = hdulist[i+1].data        
        sorted_indices = np.argsort(data['FLUX'])
        
        offset = np.mean(data['MEANROW'][sorted_indices, -20:], axis=1)        
        overscan1 = data['MEANROW'][sorted_indices, xmax] - offset
        overscan2 = data['MEANROW'][sorted_indices, xmax+1] - offset
        lastpixel = data['MEANROW'][sorted_indices, xmax-1] - offset
        cti = (overscan1+overscan2)/(xmax*lastpixel)
        flux = data['FLUX'][sorted_indices] - offset
        
        ax.loglog(lastpixel[flux <= maxflux], cti[flux <= maxflux],
                  label="Amp {0}".format(i+1), marker=marker)

    ax.axhline(y = 0.000005, color='black', linestyle='--')
    ax.set_ylim(bottom=5E-8, top=2E-4)
    ax.set_xlim(left=50.0)
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('CTI', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper right', ncol=4, fontsize=12)
    ax.set_title('CTI from EPER', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_cti.png'.format(sensor_id)))
    plt.close()
    hdulist.close()

def noise_plot(sensor_id, results_file, maxflux=150000., output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)
    
    hdulist = fits.open(results_file)
    
    for i in range(16):
        
        if i >= 10: marker = 's'
        else: marker = '^'
            
        data = hdulist[i+1].data        
        sorted_indices = np.argsort(data['FLUX'])
        
        
        noise = data['NOISE'][sorted_indices]
        flux = data['FLUX'][sorted_indices]
        
        ax.semilogx(flux[flux <= maxflux], noise[flux <= maxflux], 
                  label="Amp {0}".format(i+1), marker=marker)
        
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('Overscan Noise [e-]', fontsize=14)
    ax.set_ylim(0.0, 10.0)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'lower right', ncol=4, fontsize=12)
    ax.set_title('Overscan Noise vs. Flux', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_overscan_noise.png'.format(sensor_id)))
    plt.close()
    hdulist.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('results_dir', type=str)
    parser.add_argument('ccd', type=str)
    parser.add_argument('-f', '--maxflux', type=float, default=150000.0)
    args = parser.parse_args()

    results_dir = args.results_dir
    ccd = args.ccd
    maxflux = args.maxflux

    if ccd == 'e2v':
        xmax = 522
    elif ccd == 'itl':
        xmax = 512

    sensor_ids = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']

    for sensor_id in sensor_ids:
        output_dir = os.path.join(results_dir, sensor_id)
        results_file = os.path.join(results_dir, sensor_id, 
                                    '{0}_overscan_results.fits'.format(sensor_id))

        eper_plot(sensor_id, results_file, xmax=xmax, output_dir=output_dir)
        overscan1_plot(sensor_id, results_file, xmax=xmax, maxflux=maxflux, output_dir=output_dir)
        overscan2_plot(sensor_id, results_file, xmax=xmax, maxflux=maxflux, output_dir=output_dir)
        cti_plot(sensor_id, results_file, xmax=xmax, maxflux=maxflux, output_dir=output_dir)
        noise_plot(sensor_id, results_file, maxflux=maxflux, output_dir=output_dir)
        summedoverscan_plot(sensor_id, results_file, xmax=xmax, maxflux=maxflux, output_dir=output_dir)

    
