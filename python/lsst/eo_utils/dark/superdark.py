"""Class to construct superdark frames"""

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

from lsst.eo_utils.dark.file_utils import RAFT_DARK_TABLE_FORMATTER,\
    RAFT_DARK_PLOT_FORMATTER

from lsst.eo_utils.dark.analysis import DarkAnalysisConfig,\
    DarkAnalysisTask



class SuperdarkConfig(DarkAnalysisConfig):
    """Configuration for SuperdarkTask"""
    mask = EOUtilOptions.clone_param('mask')
    stat = EOUtilOptions.clone_param('stat')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    bitpix = EOUtilOptions.clone_param('bitpix')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='.fits')


class SuperdarkTask(DarkAnalysisTask):
    """Construct superdark frames"""

    ConfigClass = SuperdarkConfig
    _DefaultName = "SuperdarkTask"
    iteratorClass = AnalysisBySlot


    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        DarkAnalysisTask.__init__(self, **kwargs)
        self._superdark_frame = None


    def extract(self, butler, data, **kwargs):
        """Make superflat frame for one slot

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
        sdark : `dict`
            Dictionary keyed by amp of the superdark
        """
        self.safe_update(**kwargs)
        slot = self.config.slot
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        dark_files = data['DARK']
        sys.stdout.write("Working on %s, %i files." % (slot, len(dark_files)))

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        sdark = stack_images(butler, dark_files, statistic=statistic,
                             bias_type=self.config.bias, superbias_frame=superbias_frame)

        return sdark

    def make_superdark(self, butler, slot_data, **kwargs):
        """Stack the input data to make superflat frames

        The superdarks are stored as data members of this class

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

        output_file = self.get_superdark_file('').replace('.fits', '')
        makedir_safe(output_file)

        if not self.config.skip:
            sdark = self.extract(butler, slot_data)
            imutil.writeFits(sdark, output_file + '.fits', slot_data['DARK'][0], self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file + '.fits')

        self._superdark_frame = get_ccd_from_id(None, output_file + '.fits', mask_files)
        dtables = TableDict()
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots of the pixel-by-pixel distributions
        of the superdark frames

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

        if self.config.plot:
            figs.plot_sensor("img", None, self._superdark_frame)

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.extract_config_vals(default_array_kw)
            figs.histogram_array("hist", None, self._superdark_frame,
                                 title="Historam of RMS of dark-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, bins=100, range=(0., 2000,),
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

        plotbase = self.get_superdark_file('').replace('.fits', '')

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
        dtables = self.make_superdark(butler, slot_data)
        if self.config.plot is not None:
            self.make_plots(dtables)


class SuperdarkRaftConfig(DarkAnalysisConfig):
    """Configuration for SuperdarkRaftTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='raft')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    mosaic = EOUtilOptions.clone_param('mosaic')


class SuperdarkRaftTask(DarkAnalysisTask):
    """Analyze the outliers in the superdark frames for a raft"""

    ConfigClass = SuperdarkRaftConfig
    _DefaultName = "SuperdarkRaftTask"
    iteratorClass = AnalysisByRaft

    tablename_format = RAFT_DARK_TABLE_FORMATTER
    plotname_format = RAFT_DARK_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        DarkAnalysisTask.__init__(self, **kwargs)
        self._mask_file_dict = {}
        self._sdark_file_dict = {}
        self._sdark_arrays = None

    def extract(self, butler, data, **kwargs):
        """Extract the utliers in the superdark frames for the raft

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
            sys.stdout.write("Ignoring butler in extract_superbias_fft_slot\n")
        if data is not None:
            sys.stdout.write("Ignoring raft_data in extract_superbias_fft_raft\n")

        for slot in ALL_SLOTS:
            mask_files = self.get_mask_files(slot=slot)
            self._mask_file_dict[slot] = mask_files
            self._sdark_file_dict[slot] = self.get_superdark_file('', slot=slot)

        self._sdark_arrays = extract_raft_array_dict(None, self._sdark_file_dict,
                                                     mask_dict=self._mask_file_dict)

        out_data = outlier_raft_dict(self._sdark_arrays, 0., 25.)
        dtables = TableDict()
        dtables.make_datatable('outliers', out_data)
        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Plot the raft-level mosaic and histrograms
        of the numbers of outliers in the superdark frames

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
            figs.plot_raft_mosaic('mosaic', self._sdark_file_dict, bias_subtract=False)

        if self.config.stats_hist:
            figs.histogram_raft_array('stats', self._sdark_arrays,
                                      xlabel='Counts [ADU]',
                                      ylabel='Pixels',
                                      bins=100,
                                      range=(-100., 100.),
                                      histtype='step')

EO_TASK_FACTORY.add_task_class('Superdark', SuperdarkTask)
EO_TASK_FACTORY.add_task_class('SuperdarkRaft', SuperdarkRaftTask)
