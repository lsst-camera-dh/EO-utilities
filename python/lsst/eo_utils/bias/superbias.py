"""Class to construct and plot superbias frames"""

import sys

import lsst.afw.math as afwMath

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.file_utils import makedir_safe,\
    SUPERBIAS_FORMATTER

from lsst.eo_utils.base.defaults import SBIAS_TEMPLATE,\
    DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    flip_data_in_place, make_superbias

from lsst.eo_utils.base.analysis import BaseAnalysisConfig,\
    BaseAnalysisTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .file_utils import SUPERBIAS_STAT_FORMATTER

from .analysis import BiasAnalysisBySlot


class SuperbiasConfig(BaseAnalysisConfig):
    """Configuration for BiasVRowTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    suffix = EOUtilOptions.clone_param('suffix')
    mask = EOUtilOptions.clone_param('mask')
    stat = EOUtilOptions.clone_param('stat')
    bias = EOUtilOptions.clone_param('bias')
    nfiles = EOUtilOptions.clone_param('nfiles')
    bitpix = EOUtilOptions.clone_param('bitpix')


class SuperbiasTask(BaseAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = SuperbiasConfig
    _DefaultName = "SuperbiasTask"
    iteratorClass = BiasAnalysisBySlot


    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        BaseAnalysisTask.__init__(self, **kwargs)


    def extract(self, butler, data, **kwargs):
        """Make superbias frame for one slot

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Uped to override config
        """
        self.safe_update(**kwargs)
        slot = self.config.slot
        bias_type = self.config.bias
        stat_type = self.config.stat
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        bias_files = data['BIAS']

        sys.stdout.write("Working on %s, %i files.\n" % (slot, len(bias_files)))

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
        else:
            raise ValueError("Can not convert %s to a valid statistic" % stat_type)

        sbias = make_superbias(butler, bias_files, statistic=statistic, bias_type=bias_type)
        return sbias


    def make_superbias(self, butler, slot_data, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs

        @return (dict)
        """
        self.safe_update(**kwargs)

        mask_files = self.get_mask_files()
        if self.config.stat == DEFAULT_STAT_TYPE:
            formatter = SUPERBIAS_FORMATTER
            suffix = ""
        else:
            formatter = SUPERBIAS_STAT_FORMATTER
            suffix = ""

        output_file = self.get_filename_from_format(formatter, suffix)
        makedir_safe(output_file)

        if not self.config.skip:
            out_data = self.extract(butler, slot_data)
            imutil.writeFits(out_data, output_file, SBIAS_TEMPLATE, self.config.bitpix)
            if butler is not None:
                flip_data_in_place(output_file)

        sbias = get_ccd_from_id(None, output_file, mask_files)
        return sbias


    def plot(self, sbias, figs, **kwargs):
        """Make plots of the superbias frame

        @param sbias (str)          The superbias frame
        @param figs (`FigureDict`)  Place to collect figures
        @param kwargs:
            plot (bool)              Plot images of the superbias
            stats_hist (bool)        Plot statistics
        """
        self.safe_update(**kwargs)

        subtract_mean = self.config.stat == DEFAULT_STAT_TYPE

        if self.config.plot:
            figs.plot_sensor("img", None, sbias)

        default_array_kw = {}
        if self.config.stats_hist:
            kwcopy = self.config.extract_config_vals(default_array_kw)
            figs.histogram_array("hist", None, sbias,
                                 title="Historam of RMS of bias-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=subtract_mean, **kwcopy)

    def make_plots(self, sbias, **kwargs):
        """Tie together the functions to make the data tables
        @param sbias (`MaskedCCD`)   The superbias frame

        @return (`FigureDict`) the figues we produced
        """
        self.safe_update(**kwargs)

        figs = FigureDict()
        self.plot(sbias, figs)
        if self.config.plot == 'display':
            figs.save_all(None)
            return figs

        if self.config.stat == DEFAULT_STAT_TYPE:
            formatter = SUPERBIAS_FORMATTER
        else:
            formatter = SUPERBIAS_STAT_FORMATTER
        plotbase = self.get_filename_from_format(formatter, "")

        makedir_safe(plotbase)
        figs.save_all(plotbase, self.config.plot)
        return None


    def __call__(self, butler, slot_data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        self.safe_update(**kwargs)
        sbias = self.make_superbias(butler, slot_data)
        if self.config.plot is not None:
            self.make_plots(sbias)


EO_TASK_FACTORY.add_task_class('Superbias', SuperbiasTask)
