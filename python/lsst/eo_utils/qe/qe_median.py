"""Class to analyze the FFT of the bias frames"""

import numpy as np

import lsst.afw.math as afwMath

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    get_exposure_time, get_mondiode_val, get_mono_wl,\
    unbiased_ccd_image_dict

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.qe.analysis import QeAnalysisConfig, QeAnalysisTask


class QEMedianConfig(QeAnalysisConfig):
    """Configuration for QEMedianTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='qe_med')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class QEMedianTask(QeAnalysisTask):
    """Analyze some monochromatic data to extract medians """

    ConfigClass = QEMedianConfig
    _DefaultName = "QEMedianTask"
    iteratorClass = AnalysisBySlot

    def median(self, img):
        """Return the median of an image"""
        return afwMath.makeStatistics(img, afwMath.MEDIAN, self.stat_ctrl).getValue()

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

        qe_files = data['LAMBDA']

        corrections = np.ones((17))

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(qe_files))

        # This is a dictionary of dictionaries to store all the
        # data you extract from the qe_files
        data_dict = dict(WL=[], EXPTIME=[], MONDIODE=[])
        for i in range(1, 17):
            data_dict['AMP%02i_MEDIAN' % i] = []

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        for ifile, qe_file in enumerate(qe_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            ccd = get_ccd_from_id(butler, qe_file, mask_files)

            data_dict['WL'].append(get_mono_wl(ccd))
            data_dict['EXPTIME'].append(get_exposure_time(ccd))
            data_dict['MONDIODE'].append(get_mondiode_val(ccd))

            unbiased_images = unbiased_ccd_image_dict(ccd,
                                                      bias=self.config.bias,
                                                      superbias_frame=superbias_frame)


            for i, (amp, image) in enumerate(unbiased_images.items()):
                if corrections is not None:
                    image *= corrections[amp]

                value = self.median(image)
                data_dict['AMP%02i_MEDIAN' % (i+1)].append(value)

        self.log_progress("Done!")

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, qe_files))
        dtables.make_datatable('qe_med', data_dict)

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


EO_TASK_FACTORY.add_task_class('QEMedian', QEMedianTask)
