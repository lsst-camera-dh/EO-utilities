"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES, REGION_LABELS,\
    get_dimension_arrays_from_ccd, get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp

from .file_utils import get_superbias_frame,\
    slot_superbias_tablename, slot_superbias_plotname

from .analysis import BiasAnalysisFunc, BiasAnalysisBySlot

DEFAULT_BIAS_TYPE = 'spline'

class bias_struct(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['mask', 'bias', 'std', 'mask']
    analysisClass = BiasAnalysisBySlot

    def __init__(self):
        BiasAnalysisFunc.__init__(self, "biasval", self.extract, self.plot)

    @staticmethod
    def extract(butler, slot_data, **kwargs):
        """Plot the row-wise and col-wise struture
        in a series of bias frames

        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        std (bool)           Plot standard deviation instead of median
        """
        slot = kwargs['slot']
        std = kwargs.get('std', False)
        bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)

        bias_files = slot_data['BIAS']
        mask_files = get_mask_files(**kwargs)
        superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        biasstruct_data = {}

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)
            if ifile == 0:
                dim_array_dict = get_dimension_arrays_from_ccd(butler, ccd)
                for key, val in dim_array_dict.items():
                    biasstruct_data[key] = {key:val}

            bias_struct.get_ccd_data(butler, ccd, biasstruct_data,
                                     ifile=ifile, nfiles=len(bias_files),
                                     slot=slot, bias_type=bias_type,
                                     std=std, superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key, val in biasstruct_data.items():
            dtables.make_datatable('biasst-%s' % key, val)
        return dtables


    @staticmethod
    def plot(dtables, figs):
        """Plot the bias structure

        @param dtables (`TableDict`)  The data
        @param figs (`FigureDict`)    Object to store the figues
        """
        for rkey, rlabel in zip(REGION_KEYS, REGION_LABELS):
            for dkey in ['row', 'col']:
                datakey = "biasst-%s_%s" % (dkey, rkey)
                figs.setup_amp_plots_grid(datakey, title="%s, profile by %s" % (rlabel, dkey),
                                          xlabel=dkey, ylabel="ADU")
                figs.plot_xy_amps_from_tabledict(dtables, datakey, datakey,
                                                 x_name="%s_%s" % (dkey, rkey), y_name="biasst")

    @staticmethod
    def get_ccd_data(butler, ccd, data, **kwargs):
        """Get the bias values and update the data dictionary

        @param butler (`Butler`)   The data butler
        @param ccd (`MaskedCCD`)   The ccd we are getting data from
        @param data (dict)         The data we are updating
        @param kwargs:
        slot  (str)                    The slot number
        ifile (int)                    The file index
        nfiles (int)                   Total number of files
        bias_type (str)                Method to use to construct bias
        std (bool)                     Used standard deviasion instead of mean
        superbias_frame (`MaskedCCD`)  The superbias
        """
        slot = kwargs['slot']
        bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)
        ifile = kwargs.get('ifile', 0)
        nfiles = kwargs.get('nfiles', 1)
        std = kwargs.get('std', False)
        superbias_frame = kwargs.get('superbias_frame', None)

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            im = get_raw_image(butler, ccd, amp)
            if superbias_frame is not None:
                superbias_im = get_raw_image(butler, superbias_frame, amp)
            else:
                superbias_im = None
            image = unbias_amp(im, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
            frames = get_image_frames_2d(image, regions)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                framekey_row = "row_%s" % key
                framekey_col = "col_%s" % key
                struct = array_struct(frames[region], do_std=std)
                key_str = "biasst_%s_a%02i" % (slot, i)
                if key_str not in data[framekey_row]:
                    data[framekey_row][key_str] = np.ndarray((len(struct['rows']), nfiles))
                if key_str not in data[framekey_col]:
                    data[framekey_col][key_str] = np.ndarray((len(struct['cols']), nfiles))
                data[framekey_row][key_str][:, ifile] = struct['rows']
                data[framekey_col][key_str][:, ifile] = struct['cols']


class superbias_struct(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['mask', 'superbias', 'std', 'stat']
    analysisClass = BiasAnalysisBySlot

    def __init__(self):
        """C'tor"""
        BiasAnalysisFunc.__init__(self, "sbiasst", self.extract, bias_struct.plot,
                                  tablename_func=slot_superbias_tablename,
                                  plotname_func=slot_superbias_plotname)

    @staticmethod
    def extract(butler, slot_data, **kwargs):
        """Extract the row-wise and col-wise struture  in a superbias frame

        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            run_num (str)        Run number, i.e,. '6106D'
            slot (str)           Slot in question, i.e., 'S00'
            superbias (str)      Method to use for superbias subtraction
            outdir (str)         Output directory
            std (bool)           Plot standard deviation instead of median
        """
        slot = kwargs['slot']
        std = kwargs.get('std', False)

        if butler is not None:
            sys.stdout.write("Ignoring butler in extract_superbias_struct_slot")
        if slot_data is not None:
            sys.stdout.write("Ignoring butler in extract_superbias_struct_slot")

        mask_files = get_mask_files(**kwargs)
        superbias = get_superbias_frame(mask_files=mask_files, **kwargs)

        biasstruct_data = {}

        dim_array_dict = get_dimension_arrays_from_ccd(None, superbias)
        for key, val in dim_array_dict.items():
            biasstruct_data[key] = {key:val}

        bias_struct.get_ccd_data(None, superbias, biasstruct_data,
                                 slot=slot, bias_type=kwargs.get('superbias'),
                                 std=std, superbias_frame=None)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key, val in biasstruct_data.items():
            dtables.make_datatable('biasst-%s' % key, val)
        return dtables
