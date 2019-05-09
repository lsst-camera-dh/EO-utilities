"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

import lsst.eotest.image_utils as imutil

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import get_dims_from_ccd,\
    get_ccd_from_id, get_raw_image, get_geom_regions, get_amp_list

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .analysis import BiasAnalysisConfig, BiasAnalysisTask


class BiasVRowConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasval')
    bias = EOUtilOptions.clone_param('bias')


class BiasVRowTask(BiasAnalysisTask):
    """Analyze the overscan bias as a function of row number"""
    ConfigClass = BiasVRowConfig
    _DefaultName = "BiasVRowTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BiasAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the bias as function of row

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

        slot = self.config.slot

        bias_files = data['BIAS']

        sys.stdout.write("Working on %s, %i files: \n" % (slot, len(bias_files)))

        biasval_data = {}

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, [])
            if ifile == 0:
                dims = get_dims_from_ccd(butler, ccd)
                xrow_s = np.linspace(0, dims['nrow_s']-1, dims['nrow_s'])

            self.get_ccd_data(butler, ccd, biasval_data,
                              ifile=ifile, nfiles=len(bias_files))

            #Need to truncate the row array to match the data
            a_row = biasval_data[sorted(biasval_data.keys())[0]]
            biasval_data['row_s'] = xrow_s[0:len(a_row)]

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        dtables.make_datatable('biasval', biasval_data)
        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Plot the bias as function of row

        It should use a `TableDict` object to create a set of
        plots and fill a `FigureDict` object

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
        figs.setup_amp_plots_grid("biasval", title="Bias by row",
                                  xlabel="row", ylabel="Magnitude [ADU]")
        figs.plot_xy_amps_from_tabledict(dtables, 'biasval', 'biasval',
                                         x_name='row_s', y_name='biasval')


    def get_ccd_data(self, butler, ccd, data, **kwargs):
        """Get the bias values and update the data dictionary

        Parameters
        ----------
        butler : `Butler`
            The data butler
        ccd : `MaskedCCD`
            The ccd we are getting data from
        data : `dict`
            The data we are updating

        Keywords
        --------
        slot : `str`
            The slot name
        ifile : `int`
            The file index
        nfiles_used : `int`
            Total number of files
        """
        slot = self.config.slot
        bias_type = self.config.bias
        ifile = kwargs['ifile']
        nfiles = kwargs['nfiles']

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(butler, ccd, amp)
            bimg = imutil.bias_image(img, serial_oscan, bias_method=bias_type)
            bimg_row_mean = bimg[serial_oscan].getArray().mean(1)
            key_str = "biasval_%s_a%02i" % (slot, i)
            if key_str not in data:
                data[key_str] = np.ndarray((len(bimg_row_mean), nfiles))
            data[key_str][:, ifile] = bimg_row_mean


EO_TASK_FACTORY.add_task_class('BiasVRow', BiasVRowTask)
