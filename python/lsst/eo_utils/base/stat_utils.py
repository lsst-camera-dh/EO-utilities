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



def make_profile_hist(xbin_edges, xdata, ydata, **kwargs):
    """Build a profile historgram

    Parameters
    ----------
    xbin_edges : `array`
        The bin edges
    xdata : `array`
        The x-axis data
    ydata : `array`
        The y-axis data

    Keywords
    --------
    yerrs :  `array`
        The errors on the y-axis points

    stderr : `bool`
        Set error bars to standard error instead of RMS

    Returns
    -------
    x_vals : `array`
        The x-bin centers
    y_vals : `array`
        The y-bin values
    y_errs : `array`
        The y-bin errors
    """
    yerrs = kwargs.get('yerrs', None)
    stderr = kwargs.get('stderr', False)

    nbinsx = len(xbin_edges) - 1
    x_vals = (xbin_edges[0:-1] + xbin_edges[1:])/2.
    y_vals = np.ndarray((nbinsx))
    y_errs = np.ndarray((nbinsx))


    if yerrs is None:
        weights = np.ones(y_vals.shape)
    else:
        weights = 1./(yerrs*yerrs)

    y_w = ydata*weights

    for i, (xmin, xmax) in enumerate(zip(xbin_edges[0:-1], xbin_edges[1:])):
        mask = (xdata >= xmin) * (xdata < xmax)
        if mask.sum() < 2:
            y_vals[i] = 0.
            y_errs[i] = -1.
            continue
        y_vals[i] = y_w[mask].sum() / weights[mask].sum()
        y_errs[i] = ydata[mask].std()
        if stderr:
            y_errs[i] /= np.sqrt(mask.sum())

    return x_vals, y_vals, y_errs


def lin_func_1(pars, xvals):
    """Return a line whose slope is pars[0]"""
    return pars[0]*xvals

def lin_func_2(pars, xvals):
    """Return quadratic function of the form pars[0]*x + pars[1]*x*x"""
    return pars[0]*xvals + pars[1]*xvals*xvals

def lin_func_3(pars, xvals):
    """Return quadratic function of the form pars[0]*x + pars[1]*x*x + pars[2]"""
    return pars[0]*xvals + pars[1]*xvals*xvals + pars[2]

LINEARITY_FUNC_DICT = {1:lin_func_1, 2:lin_func_2, 3:lin_func_3}



def chi2_model(pars, xvals, yvals, model):
    """Return the chi2 w.r.t. the model"""
    return (yvals - model(pars, xvals))/np.sqrt(yvals)



def perform_linear_chisq_fit(xdata, ydata, fit_mask, model_func_choice):
    """Preform a linear chi**2 fit to data

    Parameters
    ----------
    xdata : `array`
        The x-axis data
    ydata : `array`
        The y-axis data
    fit_mask : `array`
        Array used to mask data
    model_func : `int`
        Function choice

    Returns
    -------
    results :
        The x-bin centers
    model_yvals : `array`
        The model values at the bins
    frac_resid : `array`
        The fractional residual
    frac_resid_err : `array`
        The uncertainty on the fractional residual
    """
    if fit_mask is not None:
        xdata_fit = xdata[fit_mask]
        ydata_fit = ydata[fit_mask]
    else:
        xdata_fit = xdata
        ydata_fit = ydata
    mean_slope = (ydata_fit/xdata_fit).mean()

    model_func = LINEARITY_FUNC_DICT[model_func_choice]

    if model_func_choice == 1:
        pars = (mean_slope,)
    elif model_func_choice == 2:
        pars = (mean_slope, 0.)
    elif model_func_choice == 3:
        pars = (mean_slope, 0., 0.)
    results = scipy.optimize.leastsq(chi2_model, pars,
                                     full_output=1,
                                     args=(xdata_fit, ydata_fit, model_func))

    model_yvals = model_func(results[0], xdata)
    frac_resid = (ydata - model_yvals)/model_yvals
    frac_resid_err = 1./ydata

    return results, model_yvals, frac_resid, frac_resid_err
