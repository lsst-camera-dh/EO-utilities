"""Class to construct and plot superbias frames"""

import sys

import lsst.afw.math as afwMath

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.file_utils import makedir_safe,\
    get_mask_files

from lsst.eo_utils.base.defaults import SBIAS_TEMPLATE,\
    DEFAULT_STAT_TYPE, DEFAULT_BITPIX

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    flip_data_in_place, make_superbias

from lsst.eo_utils.base.analysis import EO_TASK_FACTORY,\
    BaseAnalysisConfig, BaseAnalysisTask

from .file_utils import SUPERBIAS_FORMATTER, SUPERBIAS_STAT_FORMATTER

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
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            run_num (str)        Run number, i.e,. '6106D'
            slot (str)           Slot in question, i.e., 'S00'
            bias (str)           Method to use for unbiasing
            stat (str)           Statistic to use to stack data
            outdir (str)         Output directory
            bitpix (int)         Output data format BITPIX field
            skip (bool)          Flag to skip making superbias, only produce plots
            plot (bool)          Plot superbias images
            stats_hist (bool)    Plot superbias summary histograms
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

        mask_files = get_mask_files(self, **kwargs)
        if kwargs.get('stat', DEFAULT_STAT_TYPE) == DEFAULT_STAT_TYPE:
            output_file = SUPERBIAS_FORMATTER(bias_type=kwargs.get('bias'), **kwargs)
        else:
            output_file = SUPERBIAS_STAT_FORMATTER(bias_type=kwargs.get('bias'),
                                                   stat_type=kwargs.get('stat'),
                                                   **kwargs)

        makedir_safe(output_file)

        if not kwargs.get('skip', False):
            out_data = self.extract(butler, slot_data, **kwargs)
            imutil.writeFits(out_data, output_file, SBIAS_TEMPLATE,
                             kwargs.get('bitpix', DEFAULT_BITPIX))
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
        subtract_mean = self.config.stat == DEFAULT_STAT_TYPE

        if self.config.plot:
            figs.plot_sensor("img", None, sbias)

        if self.config.stats_hist:
            kwcopy = kwargs.copy()
            kwcopy.pop('bias', None)
            kwcopy.pop('superbias', None)
            figs.histogram_array("hist", None, sbias,
                                 title="Historam of RMS of bias-images, per pixel",
                                 xlabel="RMS [ADU]", ylabel="Pixels / 0.1 ADU",
                                 subtract_mean=subtract_mean, **kwcopy)

    def make_plots(self, sbias):
        """Tie together the functions to make the data tables
        @param sbias (`MaskedCCD`)   The superbias frame

        @return (`FigureDict`) the figues we produced
        """
        figs = FigureDict()
        self.plot(sbias, figs)
        return figs


    def __call__(self, butler, slot_data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        sbias = self.make_superbias(butler, slot_data, **kwargs)
        if kwargs.get('plot', False):
            figs = self.make_plots(sbias)
            if kwargs.get('interactive', False):
                figs.save_all(None)
            else:
                if kwargs.get('stat', DEFAULT_STAT_TYPE) == DEFAULT_STAT_TYPE:
                    plotbase = SUPERBIAS_FORMATTER(bias_type=kwargs.get('bias'),
                                                   **kwargs).replace('.fits', '')
                else:
                    plotbase = SUPERBIAS_STAT_FORMATTER(bias_type=kwargs.get('bias'),
                                                        stat_type=kwargs.get('stat'),
                                                        **kwargs).replace('.fits', '')

                makedir_safe(plotbase)
                figs.save_all(plotbase)


EO_TASK_FACTORY.add_task_class('Superbias', SuperbiasTask)
