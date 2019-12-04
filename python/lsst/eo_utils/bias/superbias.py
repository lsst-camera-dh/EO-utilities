"""Class to construct superbias frames"""

import os

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

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.base.merge_utils import CameraMosaicConfig, CameraMosaicTask

from lsst.eo_utils.bias.analysis import BiasAnalysisConfig, BiasAnalysisTask

from lsst.eo_utils.bias.meta_analysis import SuperbiasRaftTableAnalysisConfig,\
    SuperbiasRaftTableAnalysisTask

from lsst.eo_utils.bias.file_utils import RUN_SUPERBIAS_FORMATTER

class SuperbiasConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    stat = EOUtilOptions.clone_param('stat')
    bitpix = EOUtilOptions.clone_param('bitpix')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    filekey = EOUtilOptions.clone_param('filekey')
    vmin = EOUtilOptions.clone_param('vmin')
    vmax = EOUtilOptions.clone_param('vmax')
    nbins = EOUtilOptions.clone_param('nbins')


class SuperbiasTask(BiasAnalysisTask):
    """Construct superbias frames"""

    ConfigClass = SuperbiasConfig
    _DefaultName = "SuperbiasTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SUPERBIAS_FORMATTER

    plot_names = ['img', 'hist']

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasAnalysisTask.__init__(self, **kwargs)
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
        bias_type = self.get_bias_algo()
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        bias_files = data['BIAS']
        nbias = len(bias_files)

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
            if nbias < 3:
                self.log_warn_slot_msg(self.config, "Not enough files to stack %i < 3" % nbias)
                return None
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        self.log_info_slot_msg(self.config, "%i files" % nbias)

        sbias = stack_images(butler, bias_files, statistic=statistic, bias_type=bias_type)
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
        if not slot_data['BIAS']:
            return

        makedir_safe(output_file)

        if not self.config.skip:
            out_data = self.extract(butler, slot_data)
            if out_data is None:
                self.log_warn_slot_msg(self.config, "extract() returned None.")
                return
            if butler is None:
                template_file = slot_data['BIAS'][0]
            else:
                template_file = get_filename_from_id(butler, slot_data['BIAS'][0])

            imutil.writeFits(out_data, output_file, template_file, self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file)

        self._superbias_frame = self.get_ccd(None, output_file, mask_files)


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



class SuperbiasRaftConfig(SuperbiasRaftTableAnalysisConfig):
    """Configuration for SuperbiasRaftTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='sbias')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    mosaic = EOUtilOptions.clone_param('mosaic')


class SuperbiasRaftTask(SuperbiasRaftTableAnalysisTask):
    """Analyze the outliers in Superbias frames for a raft"""

    ConfigClass = SuperbiasRaftConfig
    _DefaultName = "SuperbiasRaftTask"

    plot_names = ['mosaic', 'stats', 'out-row', 'out-col', 'nbad', 'nbad-row', 'nbad-col']

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SuperbiasRaftTableAnalysisTask.__init__(self, **kwargs)
        self._mask_file_dict = {}
        self._sbias_file_dict = {}
        self._sbias_arrays = None
        self._sbias_images = None

    @staticmethod
    def build_defect_dict(dark_array, **kwargs):
        """Extract information about the defects into a dictionary

        Parameters
        ----------
        dark_array : `dict`
            The images, keyed by slot, amp
        kwargs
            Used to override default configuration

        Returns
        -------
        out_dict : `dict`
            The output dictionary
        """
        fp_dict = dict(slot=[],
                       amp=[],
                       x_corner=[],
                       y_corner=[],
                       x_peak=[],
                       y_peak=[],
                       x_size=[],
                       y_size=[],
                       mean_full=[])
        for i in range(4):
            fp_dict['mean_%i' % i] = []
            fp_dict['npix_%i' % i] = []
            fp_dict['npix_0p2_%i' % i] = []

        for islot, (_, slot_data) in enumerate(sorted(dark_array.items())):
            for iamp, (_, image) in enumerate(sorted(slot_data.items())):
                fill_footprint_dict(image.image, fp_dict, iamp, islot, **kwargs)
        return fp_dict


    def extract(self, butler, data, **kwargs):
        """Extract the outliers in the superbias frames for the raft

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

        self._mask_file_dict = {}
        self._sbias_file_dict = {}

        if butler is not None:
            self.log.warn("Ignoring butler")

        slot_list = self.config.slots
        if slot_list is None:
            slot_list = ALL_SLOTS
        for slot in slot_list:
            if not os.path.exists(data[slot]):
                self.log.warn("Skipping missing file for %s:%s" % (self.config.raft, slot))
                continue
            self._mask_file_dict[slot] = self.get_mask_files(slot=slot)
            self._sbias_file_dict[slot] = data[slot]


        if not self._sbias_file_dict:
            self.log.warn("No files for %s, skipping" % (self.config.raft))
            return None

        self._sbias_images, ccd_dict = extract_raft_unbiased_images(self._sbias_file_dict,
                                                                    mask_dict=self._mask_file_dict)


        self._sbias_arrays = extract_raft_imaging_data(self._sbias_images, ccd_dict)
        fp_dict = SuperbiasRaftTask.build_defect_dict(self._sbias_images, fp_type='bright', abs_thresh=50)

        out_data = outlier_raft_dict(self._sbias_arrays, 0., 10.)
        dtables = TableDict()
        dtables.make_datatable('defects', fp_dict)
        dtables.make_datatable('outliers', out_data)
        return dtables


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

        figs.make_raft_outlier_plots(dtables['outliers'])

        if self.config.skip:
            return

        if self.config.mosaic:

            figs.plot_raft_mosaic('mosaic', self._sbias_file_dict, bias_subtract=False)

        if self.config.stats_hist:
            figs.histogram_raft_array('stats', self._sbias_arrays,
                                      xlabel='Counts [ADU]',
                                      ylabel='Pixels',
                                      bins=100,
                                      range=(-100., 100.),
                                      histtype='step')



class SuperbiasMosaicConfig(CameraMosaicConfig):
    """Configuration for SuperbiasMosaicTask"""

class SuperbiasMosaicTask(CameraMosaicTask):
    """Make a mosaic from a superbias frames"""

    ConfigClass = SuperbiasMosaicConfig
    _DefaultName = "SuperbiasMosaicTask"

    intablename_format = SUPERBIAS_FORMATTER
    tablename_format = RUN_SUPERBIAS_FORMATTER
    plotname_format = RUN_SUPERBIAS_FORMATTER

    datatype = 'superbias table'



EO_TASK_FACTORY.add_task_class('Superbias', SuperbiasTask)
EO_TASK_FACTORY.add_task_class('SuperbiasRaft', SuperbiasRaftTask)
EO_TASK_FACTORY.add_task_class('SuperbiasMosaic', SuperbiasMosaicTask)
