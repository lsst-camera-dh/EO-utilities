"""Class to construct and plot superbias frames"""

import sys

import lsst.afw.math as afwMath

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.file_utils import makedir_safe,\
    get_mask_files

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.config_utils import DEFAULT_STAT_TYPE, DEFAULT_BITPIX

from lsst.eo_utils.base.plot_utils import FigureDict

from lsst.eo_utils.base.image_utils import get_ccd_from_id,\
    flip_data_in_place, make_superbias

from .file_utils import superbias_filename, superbias_stat_filename

from .analysis import BiasAnalysisBySlot

DEFAULT_BIAS_TYPE = 'spline'
SBIAS_TEMPLATE = 'analysis/superbias/templates/sbias_template.fits'


class superbias:
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['bias', 'rafts']
    analysisClass = BiasAnalysisBySlot

    @staticmethod
    def extract(butler, slot_data, **kwargs):
        """Make superbias frame for one slot

        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
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
        slot = kwargs['slot']
        bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
        stat_type = kwargs.get('stat', None)
        if stat_type is None:
            stat_type = DEFAULT_STAT_TYPE

        bias_files = slot_data['BIAS']

        sys.stdout.write("Working on %s, %i files.\n" % (slot, len(bias_files)))

        if stat_type.upper() in afwMath.__dict__:
            statistic = afwMath.__dict__[stat_type.upper()]
        else:
            raise ValueError("Can not convert %s to a valid statistic to perform stacking" % stat_type)

        sbias = make_superbias(butler, bias_files, statistic=statistic, bias_type=bias_type)
        return sbias


    def make_superbias(self, butler, slot_data, **kwargs):
        """Tie together the functions to make the data tables
        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs

        @return (dict)
        """
        
        mask_files = get_mask_files(**kwargs)
        if kwargs.get('stat', DEFAULT_STAT_TYPE) == DEFAULT_STAT_TYPE:
            output_file = superbias_filename(bias_type=kwargs.get('bias'), **kwargs)
        else:
            output_file = superbias_stat_filename(bias_type=kwargs.get('bias'), **kwargs)

        makedir_safe(output_file)

        if not kwargs.get('skip', False):
            print ("here", slot_data.keys())
            out_data = self.extract(butler, slot_data, **kwargs)
            imutil.writeFits(out_data, output_file, SBIAS_TEMPLATE, kwargs.get('bitpix', DEFAULT_BITPIX))
            if butler is not None:
                flip_data_in_place(output_file)

        sbias = get_ccd_from_id(None, output_file, mask_files)
        return sbias


    @staticmethod
    def plot(sbias, figs, **kwargs):
        """Make plots of the superbias frame

        @param sbias (str)          The superbias frame
        @param figs (`FigureDict`)  Place to collect figures
        @param kwargs:
            plot (bool)              Plot images of the superbias
            stats_hist (bool)        Plot statistics
        """
        subtract_mean = kwargs.get('stat', DEFAULT_STAT_TYPE) == DEFAULT_STAT_TYPE

        if kwargs.get('plot', False):
            figs.plot_sensor("img", None, sbias)

        if kwargs.get('stats_hist', False):
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
                plotbase = superbias_filename(**kwargs).replace('.fits', '')
                makedir_safe(plotbase)
                figs.save_all(plotbase)


    @classmethod
    def make(cls, butler, data, **kwargs):
        """Tie together the functions
        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs              Passed to the functions that do the actual work
        """
        obj = cls()
        obj(butler, data, **kwargs)

    @classmethod
    def run(cls):
        """Run the analysis"""
        functor = cls.analysisClass(cls.make, cls.argnames)
        functor.run()
