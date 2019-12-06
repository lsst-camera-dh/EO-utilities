"""Class to construct superbias frames"""

import os

import numpy as np

import lsst.afw.math as afwMath

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.file_utils import makedir_safe,\
    SUPERBIAS_FORMATTER, SUPERBIAS_STAT_FORMATTER

from lsst.eo_utils.base.butler_utils import get_filename_from_id

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.image_utils import flip_data_in_place,\
    stack_images, extract_raft_unbiased_images, extract_raft_imaging_data,\
    outlier_raft_dict, fill_footprint_dict

from lsst.eo_utils.base.iter_utils import SummaryAnalysisBySlotIterator

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.base.merge_utils import CameraMosaicConfig, CameraMosaicTask

from lsst.eo_utils.bias.meta_analysis import SuperbiasSlotTableAnalysisConfig,\
    SuperbiasSlotTableAnalysisTask

from lsst.eo_utils.bias.file_utils import RUN_SUPERBIAS_FORMATTER

class SuperbiasStabilityConfig(SuperbiasSlotTableAnalysisConfig):
    """Configuration for BiasVRowTask"""
    stat = EOUtilOptions.clone_param('stat')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    filekey = EOUtilOptions.clone_param('filekey')
    vmin = EOUtilOptions.clone_param('vmin')
    vmax = EOUtilOptions.clone_param('vmax')
    nbins = EOUtilOptions.clone_param('nbins')
    bitpix = EOUtilOptions.clone_param('bitpix')


class SuperbiasStabilityTask(SuperbiasSlotTableAnalysisTask):
    """Construct superbias frames"""

    ConfigClass = SuperbiasStabilityConfig
    _DefaultName = "SuperbiasStabilityTask"
    iteratorClass = SummaryAnalysisBySlotIterator

    tablename_format = SUPERBIAS_FORMATTER

    plot_names = ['img', 'hist']

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SuperbiasSlotTableAnalysisTask.__init__(self, **kwargs)
        self._superbias_frame = None

    def extract(self, butler, data, **kwargs):
        """Make superbias frame for one slot

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
        sbias : `dict`
            The superbias frames, keyed by amp
        """
        self.safe_update(**kwargs)
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        superbias_files = data
        nbias = len(superbias_files)

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
            if nbias < 3:
                self.log_warn_slot_msg(self.config, "Not enough files to stack %i < 3" % nbias)
                return None
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        self.log_info_slot_msg(self.config, "%i files" % nbias)

        sbias = stack_images(butler, superbias_files, statistic=statistic, bias_type=None)
        self.log_progress("Done!")
        return sbias

    def make_superbias(self, butler, slot_data, **kwargs):
        """Stack the input data to make superbias frames

        The superbias frames are stored as data members of this class

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
        self._superbias_frame = None

        mask_files = self.get_mask_files()

        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        if stat_type == DEFAULT_STAT_TYPE:
            output_file = self.tablefile_name() + '.fits'
        else:
            output_file = self.get_filename_from_format(SUPERBIAS_STAT_FORMATTER,
                                                        '.fits',
                                                        **kwargs)
        if not slot_data:
            return

        makedir_safe(output_file)

        if not self.config.skip:
            out_data = self.extract(butler, slot_data)
            if out_data is None:
                self.log_warn_slot_msg(self.config, "extract() returned None.")
                return
            if butler is None:
                template_file = slot_data[0]
            else:
                template_file = get_filename_from_id(butler, slot_data[0])

            imutil.writeFits(out_data, output_file, template_file, self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file)

        try:
            self._superbias_frame = self.get_ccd(None, output_file, mask_files)
        except Exception:
            self._superbias_frame = None



    def plot(self, dtables, figs, **kwargs):
        """Make plots of the pixel-by-pixel distributions
        of the superbias frames

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
            raise ValueError("dtables should not be set in SuperbiasTask.plot")

        if self._superbias_frame is None:
            return

        subtract_mean = self.config.stat == DEFAULT_STAT_TYPE
        if self.config.vmin is None or self.config.vmax is None:
            hist_range = None
        else:
            hist_range = (self.config.vmin, self.config.vmax)

        if self.config.plot:
            figs.plot_sensor("img", self._superbias_frame)

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.extract_config_vals(default_array_kw)
            figs.histogram_array("hist", self._superbias_frame,
                                 title="Historam of RMS of bias-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=subtract_mean, bins=self.config.nbins,
                                 range=hist_range, **kwcopy)


    def plotfile_name(self, **kwargs):
        """Get the basename for the plot files for a particular run, raft, ccd...

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The name of the file
        """
        self.safe_update(**kwargs)
        stat_type = self.config.stat
        if stat_type in [None, DEFAULT_STAT_TYPE]:
            formatter = SUPERBIAS_FORMATTER
        else:
            formatter = SUPERBIAS_STAT_FORMATTER
        return self.get_filename_from_format(formatter, '', **kwargs)


    def __call__(self, butler, slot_data, **kwargs):
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
        self.make_superbias(butler, slot_data)
        if self.config.plot is not None:
            if self._superbias_frame is None:
                self.log_info_slot_msg(self.config, "No superbias, skipping")
                return
            self.make_plots(None)




EO_TASK_FACTORY.add_task_class('SuperbiasStability', SuperbiasStabilityTask)
