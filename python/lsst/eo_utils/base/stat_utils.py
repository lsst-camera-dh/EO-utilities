"""Functions to help with statistics and fitting"""

import numpy as np

import scipy.optimize

from scipy.special import erf

SQRT2 = np.sqrt(2)

def gauss_intergral(xval, norm, x_0, sigmax):
    """Integrate Gaussian centered at (x0) with width sigmax

    Parameters
    ----------
    xval : `array`
        The bin edges
    norm : `float`
        The integral normalization
    x_0 : `float`
        Mean of the Gaussian
    sigmax : `float`
        Width of the Gaussian

    Returns
    -------
    retvals : `array`
        The values in the bins
    """
    sqrt2sigmax = SQRT2 * sigmax
    edge_vals = erf((xval - x_0)/sqrt2sigmax)
    bin_vals = 0.5 * norm * (edge_vals[1:] - edge_vals[0:-1])
    return bin_vals


def gauss_residuals(pars, bin_edges, bin_values):
    """Get the residuals w.r.t. a Gaussian

    Parameters
    ----------
    pars : `tuple`
        The parameters (norm, mean, width)
    bin_edges : `array`
        The bin edges
    bin_values : `array`
        The numbers of counts in each bin

    Returns
    -------
    retvals : `array`
        The values in the bins
    """
    errors = np.sqrt(bin_values).clip(1., np.inf)
    norm, x_0, sigmax = pars

    return (bin_values - gauss_intergral(bin_edges, norm, x_0, sigmax))/errors


def gauss_fit(hist):
    """Fit a Gaussian to a histogram

    Parameters
    ----------
    hist : `tuple`
        The output of `numpy.histogram`

    Returns
    -------
    retvals : `tuple`
        The output of `scipy.optimize.leastsq`
    """
    bin_edges = hist[1]
    bin_values = hist[0]
    norm = bin_values.sum()
    mean = (bin_edges[0] + bin_edges[-1]) / 2.
    width = (bin_edges[-1] - bin_edges[0]) / 10.
    init_pars = (norm, mean, width)
    return scipy.optimize.leastsq(gauss_residuals, init_pars,
                                  args=(bin_edges, bin_values))
