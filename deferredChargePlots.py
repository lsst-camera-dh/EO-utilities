"""
@brief Analysis plots for studying deferred charge
"""
import os
import matplotlib.pyplot as plt
import numpy as np

def eper_plot(sensor_id, results, xmin=11, xmax=521, output_dir='./'):
    """Plot of overscans as a function of flux."""

    ## Generate plots
    fig, axes = plt.subplots(4, 4, sharey=True, sharex=True, 
                             figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)
    axes = axes.flatten()

    nx = results.shape[2]
    ## Create and save overscan vs flux graphs
    target_flux_levels = [100, 1000, 10000, 25000, 50000, 75000, 100000]
    for i in range(16):
        target_flux_index = 0
        try:
            for j in range(results.shape[1]):
        
                offset = np.mean(results[i, j, -20:])
                flux = np.mean(results[i, j, xmin-1:xmax])-offset
                if flux > target_flux_levels[target_flux_index]:
                    overscan = results[i, j, xmax:]-offset
                    axes[i].plot(np.arange(xmax, nx), overscan,
                                 label='{0:d}'.format(int(round(flux, -2))))
                    axes[i].set_yscale('symlog', linthreshy=1.0)
                    axes[i].set_ylim(-2, 300)
                    axes[i].set_yticklabels([-1.0, 0.0, 1.0, 10.0, 100.0])            
                    axes[i].set_yticklabels([r'$-1$', '0', 
                                             '1', r'$10^{1}$', r'$10^{2}$'])
                    axes[i].grid(True, which='major', axis='both')
                    axes[i].set_title('Amp {0}'.format(i+1), fontsize=8)
                    axes[i].tick_params(axis='both', which='minor') 
                    if i >= 12: axes[i].set_xlabel('Pixel Number')
                    if i % 4 == 0: axes[i].set_ylabel('Signal [e-]')
                    target_flux_index += 1
                    if target_flux_index == len(target_flux_levels): break
        except Exception as e:
            print('Error occurred for Amp {0}, skipping'.format(i+1))
            print(e)
            continue
                        
    h, l = axes[-1].get_legend_handles_labels()
    fig.subplots_adjust(bottom=0.13)
    fig.legend(h, l, loc='lower center', ncol=len(target_flux_levels))
    plt.suptitle('{0} Mean Overscans'.format(sensor_id))
    plt.savefig(os.path.join(output_dir, 
                             '{0}_mean_overscan.png'.format(sensor_id)))
    plt.close()

def first_overscan_plot(sensor_id, results, xmin=11, xmax=521, output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)

    namps, nfluxes, ncols = results.shape

    for i in range(16):
        flux_array = np.empty(nfluxes)*np.nan
        oscan1_array = np.empty(nfluxes)*np.nan
        oscan2_array = np.empty(nfluxes)*np.nan

        if i >= 10:
            marker = 's'
        else:
            marker = '^'

        try:
            for j in range(results.shape[1]):
        
                offset = np.mean(results[i, j, -20:])
                flux = np.mean(results[i, j, xmin-1:xmax])-offset
                if flux <= 140000.:
                    flux_array[j] = flux
                    oscan1_array[j] = results[i, j, xmax]-offset
                    oscan2_array[j] = results[i, j, xmax+1]-offset
                else: break

            ax.loglog(flux_array, oscan1_array, 
                      label="Amp {0}".format(i+1), marker=marker)
        except:
            continue

    ax.set_ylim(bottom=max(0.01, np.min(oscan1_array)))
    ax.set_xlim(left=max(50.0, np.min(flux_array)))
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('First Overscan [e-]', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper left', ncol=4, fontsize=12)
    ax.set_title('First Overscan vs. Flux', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_first_overscan.png'.format(sensor_id)))
    plt.close()

def second_overscan_plot(sensor_id, results, xmin=11, xmax=521, output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)

    namps, nfluxes, ncols = results.shape

    for i in range(16):
        flux_array = np.empty(nfluxes)*np.nan
        oscan1_array = np.empty(nfluxes)*np.nan
        oscan2_array = np.empty(nfluxes)*np.nan

        if i >= 10:
            marker = 's'
        else:
            marker = '^'

        try:
            for j in range(results.shape[1]):
        
                offset = np.mean(results[i, j, -20:])
                flux = np.mean(results[i, j, xmin-1:xmax])-offset
                if flux <= 140000.:
                    flux_array[j] = flux
                    oscan1_array[j] = results[i, j, xmax]-offset
                    oscan2_array[j] = results[i, j, xmax+1]-offset
                else: break

            ax.loglog(flux_array, oscan2_array, 
                      label="Amp {0}".format(i+1), marker=marker)
        except:
            continue

    ax.set_ylim(bottom=max(0.01, np.min(oscan2_array)))
    ax.set_xlim(left=max(50.0, np.min(flux_array)))
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('First Overscan [e-]', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper left', ncol=4, fontsize=12)
    ax.set_title('Second Overscan vs. Flux', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_second_overscan.png'.format(sensor_id)))
    plt.close()

def cti_plot(sensor_id, results, xmin=11, xmax=521, output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)

    namps, nfluxes, ncols = results.shape

    for i in range(16):
        flux_array = np.empty(nfluxes)*np.nan
        oscan1_array = np.empty(nfluxes)*np.nan
        oscan2_array = np.empty(nfluxes)*np.nan

        if i >= 10:
            marker = 's'
        else:
            marker = '^'

        try:
            for j in range(results.shape[1]):
        
                offset = np.mean(results[i, j, -20:])
                flux = np.mean(results[i, j, xmin-1:xmax])-offset
                if flux <= 140000.:
                    flux_array[j] = flux
                    oscan1_array[j] = results[i, j, xmax]-offset
                    oscan2_array[j] = results[i, j, xmax+1]-offset
                else: break

            cti_array = (oscan1_array+oscan2_array)/(xmax*flux_array)

            ax.loglog(flux_array, cti_array, 
                      label="Amp {0}".format(i+1), marker=marker)
        except:
            continue

    ax.set_ylim(bottom=max(5E-8, np.min(cti_array)), 
                top=min(2E-4, np.max(cti_array)))
    ax.set_xlim(left=max(20.0, np.min(flux_array)))
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('CTI', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper right', ncol=4, fontsize=12)
    ax.set_title('CTI from EPER', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_cti.png'.format(sensor_id)))
    plt.close()

def oscanratio_plot(sensor_id, results, xmin=11, xmax=521, output_dir='./'):
    """Plot of the first overscan as a function of flux."""

    ## Create and save overscan pixel ratio vs flux graphs
    fig, ax = plt.subplots(1,1, figsize=(10, 8))
    fig.patch.set_facecolor('white')
    fig.patch.set_alpha(1.0)

    namps, nfluxes, ncols = results.shape

    for i in range(16):
        flux_array = np.empty(nfluxes)*np.nan
        oscan1_array = np.empty(nfluxes)*np.nan
        oscan2_array = np.empty(nfluxes)*np.nan

        if i >= 10:
            marker = 's'
        else:
            marker = '^'

        try:
            for j in range(results.shape[1]):
        
                offset = np.mean(results[i, j, -20:])
                flux = np.mean(results[i, j, xmin-1:xmax])-offset
                if flux <= 140000.:
                    flux_array[j] = flux
                    oscan1_array[j] = results[i, j, xmax]-offset
                    oscan2_array[j] = results[i, j, xmax+1]-offset
                else: break

            ratio_array = oscan2_array/(oscan1_array+oscan2_array)

            ax.semilogx(flux_array, ratio_array, 
                      label="Amp {0}".format(i+1), marker=marker)
        except:
            continue

    ax.set_ylim(bottom=max(0.0, np.min(ratio_array)),
                top=min(1.0, np.max(ratio_array)))
    ax.set_xlim(left=max(20.0, np.min(flux_array)))
    ax.grid(True, which='major', axis='both')
    ax.set_xlabel('Flux [e-]', fontsize=14)
    ax.set_ylabel('Ratio', fontsize=14)

    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc = 'upper left', ncol=4, fontsize=12)
    ax.set_title('Overscan Ratio', fontsize=18)
    plt.savefig(os.path.join(output_dir, 
                             '{0}_oscan_ratio.png'.format(sensor_id)))
    plt.close()
