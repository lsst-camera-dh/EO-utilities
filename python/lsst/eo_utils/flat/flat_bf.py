"""Class to analyze the FFT of the bias frames"""

import lsst.afw.math as afwMath

from lsst.eotest.sensor.BFTask import crossCorrelate_images

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_amp_list,\
    get_geom_regions, unbias_amp, get_raw_image

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .analysis import FlatAnalysisConfig, FlatAnalysisTask


class BFConfig(FlatAnalysisConfig):
    """Configuration for BFTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='bf')
    maxLag = EOUtilOptions.clone_param('maxLag')
    nSigmaClip = EOUtilOptions.clone_param('nSigmaClip')
    backgroundBinSize = EOUtilOptions.clone_param('backgroundBinSize')


class BFTask(FlatAnalysisTask):
    """Analyze some flat data to extract the brighter-fatter kernal"""

    ConfigClass = BFConfig
    _DefaultName = "BFTask"
    iteratorClass = AnalysisBySlot

    plot_names = []

    def mean(self, img):
        """Return the mean of an image"""
        return afwMath.makeStatistics(img, afwMath.MEAN, self.stat_ctrl).getValue()

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

        flat1_files = data['FLAT1']
        flat2_files = data['FLAT2']

        bias_type = self.get_bias_algo()
        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(flat1_files))

        # This is a dictionary of dictionaries to store all the
        # data you extract from the flat_files
        data_dict = {}
        for i in range(1, 17):
            data_dict['AMP%02i_MEAN' % i] = []
            data_dict['AMP%02i_XCORR' % i] = []
            data_dict['AMP%02i_YCORR' % i] = []
            data_dict['AMP%02i_XCORR_ERR' % i] = []
            data_dict['AMP%02i_YCORR_ERR' % i] = []

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        for ifile, (id_1, id_2) in enumerate(zip(flat1_files, flat2_files)):

            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            flat_1 = self.get_ccd(butler, id_1, [])
            flat_2 = self.get_ccd(butler, id_2, [])

            amps = get_amp_list(flat_1)

            for i, amp in enumerate(amps):
                regions = get_geom_regions(flat_1, amp)
                serial_oscan = regions['serial_overscan']
                imaging = regions['imaging']
                #imaging.grow(-20)
                im_1 = get_raw_image(flat_1, amp)
                im_2 = get_raw_image(flat_2, amp)

                superbias_im = self.get_superbias_amp_image(butler, superbias_frame, amp)

                image_1 = unbias_amp(im_1, serial_oscan, bias_type=bias_type,
                                     superbias_im=superbias_im, region=imaging).image
                image_2 = unbias_amp(im_2, serial_oscan, bias_type=bias_type,
                                     superbias_im=superbias_im, region=imaging).image

                avemean = (self.mean(image_1) + self.mean(image_2)) / 2.

                corr, corr_err = crossCorrelate_images(image_1, image_2,
                                                       self.config.maxLag,
                                                       self.config.nSigmaClip,
                                                       self.config.backgroundBinSize)

                data_dict['AMP%02i_MEAN' % (i+1)].append(avemean)
                data_dict['AMP%02i_XCORR' % (i+1)].append(corr[1][0]/corr[0][0])
                data_dict['AMP%02i_YCORR' % (i+1)].append(corr[0][1]/corr[0][0])
                data_dict['AMP%02i_XCORR_ERR' % (i+1)].append(corr_err[1][0])
                data_dict['AMP%02i_YCORR_ERR' % (i+1)].append(corr_err[0][1])

        self.log_progress("Done!")

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, flat1_files + flat2_files))
        dtables.make_datatable('bf', data_dict)

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



EO_TASK_FACTORY.add_task_class('BF', BFTask)
