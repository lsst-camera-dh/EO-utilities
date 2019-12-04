"""This module contains functions merge fits files

Based on code by Seth Digel
"""
# merge_superdark.py  28 Oct 2019

import numpy as np

from astropy.io import fits

from scipy.interpolate import RectBivariateSpline

from .config_utils import EOUtilOptions

from .file_utils import makedir_safe

from .analysis import AnalysisTask, AnalysisConfig

from .iter_utils import TableAnalysisByRun


# Below from https://scipy-cookbook.readthedocs.io/items/Rebinning.html
def _rebin(arr, *args):
    shape = arr.shape
    len_shape = len(shape)
    factor = np.asarray(shape)/np.asarray(args)
    ev_list = ['arr.reshape('] + \
        ['args[%d],int(factor[%d]),'%(i, i) for i in range(len_shape)] + \
        [')'] + ['.mean(%d)'%(i+1) for i in range(len_shape)]
    return eval(''.join(ev_list))

def _assemble_clean(file, gains=None):
    # Reads and assembles 16 MEF FITS image into a single image, trimming the
    # prescan/overscan regions
    hdu = fits.open(file)

    # Get the assembled size of the image
    detsize = hdu[0].header['detsize']
    n_x = int(detsize.split(':')[1].split(',')[0])
    n_y = int(detsize.split(':')[2].split(']')[0])
    imarr = np.zeros((n_y, n_x))

    for i in range(1, 17):
        img = hdu[i].data

        if gains is not None:
            img *= gains[i-1]

        seg = int(hdu[i].header['extname'][7:])
        detsec = hdu[i].header['detsec']
        datasec = hdu[i].header['datasec']
        x1d = int(datasec[1:].split(':')[0]) - 1
        x2d = int(datasec.split(':')[1].split(',')[0]) - 1
        y1d = int(datasec.split(',')[1].split(':')[0]) - 1
        y2d = int(datasec.split(':')[2].split(']')[0]) - 1
        x_1 = int(detsec[1:].split(':')[0]) - 1
        x_2 = int(detsec.split(':')[1].split(',')[0]) - 1
        y_1 = int(detsec.split(',')[1].split(':')[0]) - 1
        y_2 = int(detsec.split(':')[2].split(']')[0]) - 1

        xdim = np.abs(x_2 - x_1) + 1
        ydim = np.abs(y_2 - y_1) + 1
        if seg >= 10:
            xoff = (seg - 10)*xdim
            yoff = 0
        else:
            xoff = seg*xdim
            yoff = ydim

        if x_2 < x_1:
            im2 = np.fliplr(img[:, x1d:x2d+1])
        else:
            im2 = img[:, x1d:x2d+1]
        if y_2 < y_1:
            im3 = np.flipud(im2[y1d:y2d+1, :])
        else:
            im3 = im2[y1d:y2d+1, :]

        imarr[yoff:(yoff+ydim), xoff:(xoff+xdim)] = im3

    imarr = np.fliplr(imarr)
    return imarr


def _make_ccd_hdu(image, raft, slot):

    # Define header keywords (WCSQ equivalent)
    r_x = int(raft[2])
    r_y = int(raft[1])
    s_x = int(slot[2])
    s_y = int(slot[1])

    hdu_new = fits.ImageHDU(np.rot90(image, 2))  # include rotation by 180 deg for display in ds9
    hdu_new.header['extname'] = raft + '_' + slot
    hdu_new.header['crval1q'] = r_x*12700/16. + s_x*4225/16.  # 12700 pixels is raft pitch, 4225 is CCD pitch
    hdu_new.header['cdelt1q'] = 1
    hdu_new.header['crpix1q'] = 0
    hdu_new.header['crval2q'] = r_y*12700/16. + s_y*4225/16.
    hdu_new.header['cdelt2q'] = 1
    hdu_new.header['crpix2q'] = 0
    hdu_new.header['pc1_1q'] = 1
    hdu_new.header['pc1_2q'] = 0
    hdu_new.header['pc2_1q'] = 0
    hdu_new.header['pc2_2q'] = 1
    hdu_new.header['WCSNAMEQ'] = 'RAFT_SERPAR'#        / Name of coordinate system
    hdu_new.header['CTYPE1Q'] = 'RAFT_S  '    #       / In the serial-parallel coordinate system
    hdu_new.header['CTYPE2Q'] = 'RAFT_P  '    #       / In
    return hdu_new


def merge_fp(in_dict, for_whom=None):
    """Merge a fits HDU from a set of files into a single HDUList"""
    # Define pixel coordinate ranges for the interpolated image
    # (The dimensions were chosen to be approximately the same size as both e2v and ITL CCDs but also
    # divisible by 16 in both x and y.)
    xaxis = np.arange(4064)
    yaxis = np.arange(4000)

    header = fits.PrimaryHDU()
    hdu_out = fits.HDUList([header])

    if for_whom is not None:
        for_whom.log.info("Merging Focal plane")

    for raft, raft_data in sorted(in_dict.items()):

        if for_whom is not None:
            for_whom.log.info("  %s" % raft)


        for slot, infile in sorted(raft_data.items()):

            if for_whom is not None:
                for_whom.log.info("    %s" % slot)

            try:
                # Trim the overscan and assemble the image
                image = _assemble_clean(infile)
            except Exception:
                print("Skipping %s %s" % (slot, infile))
                continue

            # Regrid to 4000x4064
            # see https://scipython.com/book/chapter-8-scipy/examples/two-dimensional-interpolation-with-scipyinterpolategriddata/
            x_1 = np.arange(image.shape[0])
            y_1 = np.arange(image.shape[1])

            # see https://scipython.com/book/chapter-8-scipy/examples/two-dimensional-interpolation-with-scipyinterpolaterectbivariatespline/
            interp_spline = RectBivariateSpline(x_1, y_1, image)
            image2 = interp_spline(yaxis, xaxis)  # note the order of the arguments

            # Bin down to 250x254
            image3 = _rebin(image2, 250, 254)
            hdu_new = _make_ccd_hdu(image3, raft, slot)

            # Append HDU to the output file
            hdu_out.append(hdu_new)

    return hdu_out







class CameraMosaicConfig(AnalysisConfig):
    """Configuration for CameraMosaicTask"""
    run = EOUtilOptions.clone_param('run')
    infilekey = EOUtilOptions.clone_param('infilekey')
    vmin = EOUtilOptions.clone_param('vmin', default=-10)
    vmax = EOUtilOptions.clone_param('vmax', default=10.)


class CameraMosaicTask(AnalysisTask):
    """Make a camera level mosaic"""

    ConfigClass = CameraMosaicConfig
    _DefaultName = "CameraMosaicTask"

    iteratorClass = TableAnalysisByRun

    plot_names = ['mosaic']

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)
        self._hdu_out = None

    def extract(self, butler, data, **kwargs):
        """Make a camera level mosaic

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        self.safe_update(**kwargs)

        if butler is not None:
            self.log.warn("Ignoring butler")

        hdu_out = merge_fp(data, self)
        output_file = self.tablefile_name() + '.fits'

        makedir_safe(output_file)
        hdu_out.writeto(output_file, overwrite=True)
        return hdu_out


    def plot(self, dtables, figs, **kwargs):
        """Plot the raft-level mosaic and histrograms
        of the numbers of outliers in the superbias frames

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)

        if dtables is not None:
            raise ValueError("dtables should not be set in SuperbiasRunTask.plot")

        figs.plot_reduced_focal_plane_mosaic('mosaic', self._hdu_out,
                                             vmin=self.config.vmin, vmax=self.config.vmax)


    def __call__(self, butler, data, **kwargs):
        """Tie together analysis functions

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)

        if self.config.skip:
            output_file = self.tablefile_name() + '.fits'
            try:
                self._hdu_out = fits.open(output_file)
            except Exception as msg:
                print(msg)
                self._hdu_out = None
        else:
            self._hdu_out = self.extract(butler, data, **kwargs)

        if self._hdu_out is None:
            self.log.warn("No data")

        if self.config.plot is not None:
            self.make_plots(None)

        self._hdu_out.close()
