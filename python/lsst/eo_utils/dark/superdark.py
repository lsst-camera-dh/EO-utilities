"""Class to construct superdark frames"""

import os

import lsst.afw.math as afwMath

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.file_utils import makedir_safe

from lsst.eo_utils.base.butler_utils import get_filename_from_id

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, stack_summary_table,\
    get_run_config_table

from lsst.eo_utils.base.plot_utils import plot_outlier_summary

from lsst.eo_utils.base.image_utils import flip_data_in_place,\
    stack_images, extract_raft_unbiased_images, extract_raft_imaging_data,\
    outlier_raft_dict, build_defect_dict

from lsst.eo_utils.bias.analysis import AnalysisTask

from lsst.eo_utils.base.iter_utils import AnalysisBySlot,\
    TableAnalysisByRaft

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.dark.file_utils import RAFT_SDARK_TABLE_FORMATTER,\
    RAFT_SDARK_PLOT_FORMATTER, SUPERDARK_FORMATTER, SUPERDARK_STAT_FORMATTER,\
    RUN_SUPERDARK_FORMATTER, RUN_SUPERDARK_STAT_FORMATTER

from lsst.eo_utils.base.merge_utils import CameraMosaicConfig, CameraMosaicTask

from lsst.eo_utils.dark.analysis import DarkAnalysisConfig,\
    DarkAnalysisTask

from lsst.eo_utils.dark.meta_analysis import SuperdarkSummaryAnalysisConfig, SuperdarkSummaryAnalysisTask


class SuperdarkConfig(DarkAnalysisConfig):
    """Configuration for SuperdarkTask"""
    stat = EOUtilOptions.clone_param('stat')
    bitpix = EOUtilOptions.clone_param('bitpix')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    filekey = EOUtilOptions.clone_param('filekey')


class SuperdarkTask(DarkAnalysisTask):
    """Construct superdark frames"""

    ConfigClass = SuperdarkConfig
    _DefaultName = "SuperdarkTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SUPERDARK_FORMATTER

    plot_names = ['img', 'hist']

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
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        dark_files = data['DARK']

        self.log_info_slot_msg(self.config, "%i files" % len(dark_files))

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        sdark = stack_images(butler, dark_files, statistic=statistic,
                             bias_type=self.get_bias_algo(), bias_type_col=self.get_bias_col_algo(),
                             superbias_frame=superbias_frame)
        self.log_progress("Done!")
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

        output_file = self.tablefile_name() + '.fits'

        if not slot_data['DARK']:
            return

        makedir_safe(output_file)

        if not self.config.skip:
            sdark = self.extract(butler, slot_data)
            if butler is None:
                template_file = slot_data['DARK'][0]
            else:
                template_file = get_filename_from_id(butler, slot_data['DARK'][0])

            imutil.writeFits(sdark, output_file, template_file, self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file)

        self._superdark_frame = self.get_ccd(None, output_file, mask_files)


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

        if dtables is not None:
            raise ValueError("dtables should not be set in SuperdarkTask.plot")

        if self.config.plot:
            figs.plot_sensor("img", self._superdark_frame)

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.extract_config_vals(default_array_kw)
            figs.histogram_array("hist", self._superdark_frame,
                                 title="Historam of RMS of dark-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=False, bins=100, range=(-100., 100,),
                                 **kwcopy)

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
        return self.get_superdark_file().replace('.fits', '')


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
        self.make_superdark(butler, slot_data)
        if self.config.plot is not None:
            self.make_plots(None)


class SuperdarkRaftConfig(DarkAnalysisConfig):
    """Configuration for SuperdarkRaftTask"""
    filekey = EOUtilOptions.clone_param('filekey', default='sdark')
    infilekey = EOUtilOptions.clone_param('infilekey')
    slots = EOUtilOptions.clone_param('slots')
    stats_hist = EOUtilOptions.clone_param('stats_hist')
    mosaic = EOUtilOptions.clone_param('mosaic')


class SuperdarkRaftTask(AnalysisTask):
    """Analyze the outliers in the superdark frames for a raft"""

    ConfigClass = SuperdarkRaftConfig
    _DefaultName = "SuperdarkRaftTask"
    iteratorClass = TableAnalysisByRaft

    intablename_format = SUPERDARK_FORMATTER
    tablename_format = RAFT_SDARK_TABLE_FORMATTER
    plotname_format = RAFT_SDARK_PLOT_FORMATTER

    plot_names = ['mosaic', 'stats', 'out-row', 'out-col', 'nbad', 'nbad-row', 'nbad-col']

    datatype = "dark"

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)
        self._mask_file_dict = {}
        self._sdark_file_dict = {}
        self._sdark_images = None
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

        self._mask_file_dict = {}
        self._sdark_file_dict = {}

        if butler is not None:
            self.log.warn("Ignoring butler")

        self.set_local_data(butler, data, **kwargs)

        if not self._sdark_file_dict:
            self.log.warn("No files for %s, skipping" % (self.config.raft))
            return None

        self._sdark_images, ccd_dict = extract_raft_unbiased_images(self._sdark_file_dict,
                                                                    mask_dict=self._mask_file_dict)

        self._sdark_arrays = extract_raft_imaging_data(self._sdark_images, ccd_dict)

        out_data = outlier_raft_dict(self._sdark_arrays, 0., 25.)

        fp_dict = build_defect_dict(self._sdark_images, fp_type='bright', abs_thresh=50)

        dtables = TableDict()
        dtables.make_datatable('defects', fp_dict)
        dtables.make_datatable('outliers', out_data)
        return dtables


    def set_local_data(self, butler, data, **kwargs):
        """Set local data members if extract fails

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
        slots = self.config.slots
        if slots is None:
            slots = ALL_SLOTS

        for slot in slots:
            if not os.path.exists(data[slot]):
                self.log.warn("skipping missing data for %s:%s" % (self.config.raft, slot))
                continue
            mask_files = self.get_mask_files(slot=slot)
            self._mask_file_dict[slot] = mask_files
            self._sdark_file_dict[slot] = data[slot]



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


class SuperdarkOutlierSummaryConfig(SuperdarkSummaryAnalysisConfig):
    """Configuration for SuperdarkOutlierSummaryTask"""
    infilekey = EOUtilOptions.clone_param('infilekey', default='sdark')
    filekey = EOUtilOptions.clone_param('filekey', default='sdark-sum')

class SuperdarkOutlierSummaryTask(SuperdarkSummaryAnalysisTask):
    """Summarize the results for the superbias outlier analysis"""

    ConfigClass = SuperdarkOutlierSummaryConfig
    _DefaultName = "SuperdarkOutlierSummaryTask"

    plot_names = []

    def extract(self, butler, data, **kwargs):
        """Make a summry table of the bias FFT data

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
            self.log.warn("Ignoring butler in extract()")

        dtables = stack_summary_table(data, self,
                                      tablename='outliers',
                                      keep_cols=['nbad_total', 'nbad_rows', 'nbad_cols', 'slot', 'amp'])
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the summary data from the superbias statistics study

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
        config_table = get_run_config_table(kwargs.get('config_table', 'dark_config.fits'), 'config')
        plot_outlier_summary(self, dtables, figs, config_table, "config")


class SuperdarkMosaicConfig(CameraMosaicConfig):
    """Configuration for SuperdarkMosaicTask"""

class SuperdarkMosaicTask(CameraMosaicTask):
    """Make a mosaic from a superbias frames"""

    ConfigClass = SuperdarkMosaicConfig
    _DefaultName = "SuperdarkMosaicTask"

    intablename_format = SUPERDARK_FORMATTER
    tablename_format = RUN_SUPERDARK_FORMATTER
    plotname_format = RUN_SUPERDARK_FORMATTER

    datatype = 'superdark'


class SuperdarkStatMosaicConfig(CameraMosaicConfig):
    """Configuration for SuperdarkMosaicTask"""
    stat = EOUtilOptions.clone_param('stat', default='stdevclip')


class SuperdarkStatMosaicTask(CameraMosaicTask):
    """Make a mosaic from a superbias frames"""

    ConfigClass = SuperdarkStatMosaicConfig
    _DefaultName = "SuperdarkMosaicTask"

    intablename_format = SUPERDARK_STAT_FORMATTER
    tablename_format = RUN_SUPERDARK_STAT_FORMATTER
    plotname_format = RUN_SUPERDARK_STAT_FORMATTER

    datatype = 'superdark'




EO_TASK_FACTORY.add_task_class('Superdark', SuperdarkTask)
EO_TASK_FACTORY.add_task_class('SuperdarkRaft', SuperdarkRaftTask)
EO_TASK_FACTORY.add_task_class('SuperdarkOutlierSummary', SuperdarkOutlierSummaryTask)
EO_TASK_FACTORY.add_task_class('SuperdarkMosaic', SuperdarkMosaicTask)
EO_TASK_FACTORY.add_task_class('SuperdarkStatMosaic', SuperdarkStatMosaicTask)
