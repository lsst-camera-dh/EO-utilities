"""Class to analyze the FFT of the bias frames"""

import sys

#import matplotlib.pyplot as plt

import numpy as np

import lsst.afw.geom as afwGeom

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, construct_bbox_dict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    get_exposure_time, get_mondiode_val,\
    unbiased_ccd_image_dict

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.flat.analysis import FlatAnalysisConfig, FlatAnalysisTask

#from lsst.eo_utils.flat.file_utils import SLOT_FLAT_TABLE_FORMATTER,\
#    RAFT_FLAT_TABLE_FORMATTER, RAFT_FLAT_PLOT_FORMATTER

from lsst.eo_utils.sflat.file_utils import RAFT_SFLAT_TABLE_FORMATTER

from lsst.pex.exceptions import LengthError


class DustLinearityAnalysisConfig(FlatAnalysisConfig):
    """Configuration for dustLinearityAnalysisTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='dust_linearity')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class DustLinearityAnalysisTask(FlatAnalysisTask):
    """Analyze some linearity data"""

    ConfigClass = DustLinearityAnalysisConfig
    _DefaultName = "dustLinearityAnalysisTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        FlatAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract data

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
            Output data tables
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        flat1_files = data['FLAT1']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(flat1_files))

        sflat_table_file = self.get_filename_from_format(RAFT_SFLAT_TABLE_FORMATTER, "sflat.fits")

        sflat_tables = TableDict(sflat_table_file)
        # dictionary of dictionaries of lists of bounding
        # boxes, keyed by slot, amp
        bbox_dict = construct_bbox_dict(sflat_tables['defects'])

        slot_bbox_dict = bbox_dict[slot]
        slot_idx_dict = dict(S00=0, S01=1, S02=2, S10=3, S11=4, S12=5, S20=6, S21=7, S22=8)

        # This is a dictionary of dictionaries to store all the
        # data you extract from the flat1_files

        fp_dict = dict(slot=[],
                       amp=[],
                       x_corner=[],
                       y_corner=[],
                       x_size=[],
                       y_size=[],
                       med_flux_full=[],
                       exptime=[],
                       mondiode=[],
                       amp_median=[],
                       ratio_full=[])
        for i in range(4):
            fp_dict['ratio_%i' % i] = []
            fp_dict['med_flux_%i' % i] = []
            fp_dict['npix_%i' % i] = []
            fp_dict['npix_0p2_%i' % i] = []


        # Analysis goes here, you should fill fp_dict with data extracted
        # by the analysis
        #
        for ifile, flat1_file in enumerate(flat1_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            ccd = get_ccd_from_id(butler, flat1_file, mask_files)

            # To be appended while looping over bounding boxes
            exptime = get_exposure_time(ccd)
            mondiode_val = get_mondiode_val(ccd)
            islot = slot_idx_dict[slot]

            unbiased_images = unbiased_ccd_image_dict(ccd,
                                                      bias=self.config.bias,
                                                      superbias_frame=superbias_frame)

            for iamp, (amp, image) in enumerate(unbiased_images.items()):

                bbox_list = slot_bbox_dict[iamp]
                amp_median = np.median(image.array)
                #fill fp_dict
                frac_thresh = kwargs.get('frac_thresh', 0.9)

                thresh_float = frac_thresh*amp_median
                thresh_0p2_float = (1. - (1. - frac_thresh)*0.2)*amp_median

                max_bbox = min(len(bbox_list), 10)
                #print(i, amp, bbox_list[0:max_bbox])
                #print(max_bbox)
                for bbox in bbox_list[0:max_bbox]:

                    try:
                        cutout = image[bbox].array
                    except Exception:
                        print("cutout failed", slot, amp, bbox)
                        continue
                    #print(ifile, bbox, cutout)


                    ratio_full = np.mean(cutout)/amp_median
                    cutout_median_full = np.median(cutout)

                    peak_idx = cutout.argmax()

                    peak_x = bbox.getMinX() + int(peak_idx % cutout.shape[1])
                    peak_y = bbox.getMinY() + int(peak_idx / cutout.shape[1])

                    peak = afwGeom.Point2I(peak_x, peak_y)
                    extent = afwGeom.Extent2I(1, 1)
                    bbox_expand = afwGeom.Box2I(peak, extent)

                    #npix = np.array([1, 9, 25, 49])
                    npix_cumul = np.array([1, 8, 16, 24])
                    sums = np.zeros((4))
                    meds = np.zeros((4))
                    over_thresh = np.zeros((4), int)
                    over_0p2_thresh = np.zeros((4), int)

                    sums_cumul = np.zeros((4))
                    meds_cumul = np.zeros((4))
                    over_thresh_cumul = np.zeros((4), int)
                    over_0p2_thresh_cumul = np.zeros((4), int)

                    for j in range(4):

                        try:
                            cuttout_array = image[bbox_expand].array
                        except LengthError:
                            break

                        sums[j] = cuttout_array.sum()
                        meds[j] = np.median(cuttout_array)
                        over_thresh[j] = (cuttout_array > thresh_float).sum()
                        over_0p2_thresh[j] = (cuttout_array > thresh_0p2_float).sum()

                        if j > 0:
                            sums_cumul[j] = sums[j] - sums[j-1]
                            meds_cumul[j] = meds[j] - meds[j - 1]
                            over_thresh_cumul[j] = over_thresh[j] - over_thresh[j-1]
                            over_0p2_thresh_cumul[j] = over_0p2_thresh[j] - over_0p2_thresh[j-1]
                        else:
                            sums_cumul[j] = sums[j]
                            meds_cumul[j] = meds[j]
                            over_thresh_cumul[j] = over_thresh[j]
                            over_0p2_thresh_cumul[j] = over_0p2_thresh[j]

                        bbox_expand.grow(1)

                    means_cumul = sums_cumul/(npix_cumul*amp_median)

                    fp_dict['exptime'].append(exptime)
                    fp_dict['mondiode'].append(mondiode_val)
                    fp_dict['amp'].append(iamp)
                    fp_dict['slot'].append(islot)
                    fp_dict['amp_median'].append(amp_median)
                    fp_dict['x_corner'].append(bbox.getMinX())
                    fp_dict['y_corner'].append(bbox.getMinY())

                    fp_dict['x_size'].append(bbox.getWidth())
                    fp_dict['y_size'].append(bbox.getHeight())

                    fp_dict['med_flux_full'].append(cutout_median_full)
                    fp_dict['ratio_full'].append(ratio_full)


                    for i in range(4):
                        fp_dict['ratio_%i' % i].append(means_cumul[i])
                        fp_dict['med_flux_%i' % i].append(meds_cumul[i])
                        fp_dict['npix_%i' % i].append(over_thresh_cumul[i])
                        fp_dict['npix_0p2_%i' % i].append(over_0p2_thresh_cumul[i])


        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, flat1_files))
        dtables.make_datatable('footprints', fp_dict)

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots

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

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs

        fp_table = dtables['footprints']

        figs.setup_amp_plots_grid('dust_linearity',
                                  title="Median signal at dust spot by amp median",
                                  xlabel="amp flux", ylabel="dust flux")


        for iax, axes in enumerate(figs['dust_linearity']['axs'].ravel()):
            axes.scatter(fp_table[fp_table['amp'] == iax]['amp_median'],
                         fp_table[fp_table['amp'] == iax]['med_flux_full'])


EO_TASK_FACTORY.add_task_class('DustLinearityAnalysis', DustLinearityAnalysisTask)
