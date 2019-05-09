"""Class to construct superbias frames"""

import sys

import lsst.afw.math as afwMath

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.file_utils import makedir_safe

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    flip_data_in_place, stack_images, extract_raft_array_dict,\
    outlier_raft_dict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot,\
    AnalysisByRaft

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias.analysis import BiasAnalysisConfig,\
    BiasAnalysisTask

from lsst.eo_utils.bias.file_utils import RAFT_BIAS_TABLE_FORMATTER,\
    RAFT_BIAS_PLOT_FORMATTER


class SuperbiasConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    mask = EOUtilOptions.clone_param('mask')
    stat = EOUtilOptions.clone_param('stat')
    bias = EOUtilOptions.clone_param('bias')
    bitpix = EOUtilOptions.clone_param('bitpix')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='.fits')


class SuperbiasTask(BiasAnalysisTask):
    """Construct superbias frames"""

    ConfigClass = SuperbiasConfig
    _DefaultName = "SuperbiasTask"
    iteratorClass = AnalysisBySlot


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
        slot = self.config.slot
        bias_type = self.config.bias
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        bias_files = data['BIAS']

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        sbias = stack_images(butler, bias_files, statistic=statistic, bias_type=bias_type)
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

        mask_files = self.get_mask_files()
        output_file = self.get_superbias_file('.fits', superbias=self.config.bias)
        makedir_safe(output_file)

        if not self.config.skip:
            out_data = self.extract(butler, slot_data)
            imutil.writeFits(out_data, output_file, slot_data['BIAS'][0], self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file)

        self._superbias_frame = get_ccd_from_id(None, output_file, mask_files)
        dtables = TableDict()
        return dtables


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

        if dtables.keys():
            raise ValueError("dtables should not be set")

        subtract_mean = self.config.stat == DEFAULT_STAT_TYPE

        if self.config.plot:
            figs.plot_sensor("img", None, self._superbias_frame)

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.extract_config_vals(default_array_kw)
            figs.histogram_array("hist", None, self._superbias_frame,
                                 title="Historam of RMS of bias-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=subtract_mean, bins=100, range=(0., 2000,),
                                 **kwcopy)


    def make_plots(self, dtables, **kwargs):
        """Tie together the functions to make the figures

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task

        Returns
        -------
        figs : `FigureDict`
            The resulting figures
        """
        self.safe_update(**kwargs)

        figs = FigureDict()
        self.plot(dtables, figs)
        if self.config.plot == 'display':
            figs.save_all(None)
            return figs

        plotbase = self.get_superbias_file('', superbias=self.config.bias)

        makedir_safe(plotbase)
        figs.save_all(plotbase, self.config.plot)
        return None

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
        dtables = self.make_superbias(butler, slot_data)
        if self.config.plot is not None:
            self.make_plots(dtables)



class SuperbiasRaftConfig(BiasAnalysisConfig):
    """Configuration for SuperbiasRaftTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='raft')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    mosaic = EOUtilOptions.clone_param('mosaic')


class SuperbiasRaftTask(BiasAnalysisTask):
    """Analyze the correlations between the overscans for all amplifiers on a raft"""

    ConfigClass = SuperbiasRaftConfig
    _DefaultName = "SuperbiasRaftTask"
    iteratorClass = AnalysisByRaft

    tablename_format = RAFT_BIAS_TABLE_FORMATTER
    plotname_format = RAFT_BIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasAnalysisTask.__init__(self, **kwargs)
        self._mask_file_dict = {}
        self._sbias_file_dict = {}
        self._sbias_arrays = None

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

        if butler is not None:
            sys.stdout.write("Ignoring butler in SuperbiasRaft\n")
        if data is not None:
            sys.stdout.write("Ignoring raft_data in SuperbiasRaft\n")

        for slot in ALL_SLOTS:
            self._mask_file_dict[slot] = self.get_mask_files(slot=slot)
            self._sbias_file_dict[slot] = self.get_superbias_file('.fits', slot=slot)

        self._sbias_arrays = extract_raft_array_dict(None, self._sbias_file_dict,
                                                     mask_dict=self._mask_file_dict)


        out_data = outlier_raft_dict(self._sbias_arrays, 0., 10.)
        dtables = TableDict()
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


EO_TASK_FACTORY.add_task_class('Superbias', SuperbiasTask)
EO_TASK_FACTORY.add_task_class('SuperbiasRaft', SuperbiasRaftTask)
