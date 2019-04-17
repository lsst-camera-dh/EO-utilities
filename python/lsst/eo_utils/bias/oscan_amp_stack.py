
"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.defaults import DEFAULT_BIAS_TYPE

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import  REGION_KEYS,\
    get_ccd_from_id, get_dimension_arrays_from_ccd

from .file_utils import get_superbias_frame

from .data_utils import stack_by_amps

from .data_utils import convert_stack_arrays_to_dict

from .analysis import BiasAnalysisFunc, BiasAnalysisBySlot


class oscan_amp_stack(BiasAnalysisFunc):
    """Class to analyze correlations between the imaging section
    and the overscan regions in a series of bias frames"""

    argnames = STANDARD_SLOT_ARGS + ['bias', 'rafts', 'superbias', 'mask']
    iteratorClass = BiasAnalysisBySlot

    def __init__(self):
        BiasAnalysisFunc.__init__(self, "biasosstack")

    @staticmethod
    def extract(butler, data, **kwargs):
        """Stack the overscan region from all the amps on a sensor
        to look for coherent read noise

        @param butler (Butler)   The data butler
        @param data (dict)       Dictionary pointing to the bias and mask files
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            bias (str)           Method to use for unbiasing
            superbias (str)      Method to use for superbias subtraction
        """
        slot = kwargs['slot']
        bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)

        bias_files = data['BIAS']
        mask_files = get_mask_files(**kwargs)
        superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        stack_arrays = {}

        nfiles = len(bias_files)

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)

            if ifile == 0:
                dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)
                for key, val in dim_array_dict.items():
                    stack_arrays[key] = np.zeros((nfiles, 16, len(val)))

            stack_by_amps(stack_arrays, butler, ccd,
                          ifile=ifile, bias_type=bias_type,
                          superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        stackdata_dict = convert_stack_arrays_to_dict(stack_arrays, dim_array_dict, nfiles)

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key, val in stackdata_dict.items():
            dtables.make_datatable('stack-%s' % key, val)
        return dtables


    @staticmethod
    def plot(dtables, figs):
        """Plot the bias structure

        @param dtables (TableDict)  The data
        @param figs (FigureDict)    Object to store the figues
        """
        stats = ['mean', 'std', 'signif']
        stats_labels = ['Mean [ADU]', 'Std [ADU]', 'Significance [sigma]']
        for skey, slabel in zip(stats, stats_labels):
            y_name = "stack_%s" % skey
            figkey = "biasosstack-%s" % skey
            figs.setup_region_plots_grid(figkey, title=stats,
                                         xlabel="Channel", ylabel=slabel)

            idx = 0
            for rkey in REGION_KEYS:
                for dkey in ['row', 'col']:
                    xkey = "%s_%s" % (dkey, rkey)
                    datakey = "stack-%s" % xkey
                    figs.plot_xy_axs_from_tabledict(dtables, datakey, idx, figkey,
                                                    x_name=xkey, y_name=y_name)
                    idx += 1
