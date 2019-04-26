"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES, REGION_LABELS,\
    get_dimension_arrays_from_ccd, get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp

from lsst.eo_utils.base.analysis import EO_TASK_FACTORY

from .file_utils import get_superbias_frame,\
    SLOT_SBIAS_TABLE_FORMATTER, SLOT_SBIAS_PLOT_FORMATTER

from .analysis import BiasAnalysisTask, BiasAnalysisConfig, BiasAnalysisBySlot


class BiasStructConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    suffix = EOUtilOptions.clone_param('suffix', default='biasst')
    bias = EOUtilOptions.clone_param('bias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')


class BiasStructTask(BiasAnalysisTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = BiasStructConfig
    _DefaultName = "BiasStructTask"
    iteratorClass = BiasAnalysisBySlot

    def __init__(self, **kwargs):
        """ C'tor """
        BiasAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Plot the row-wise and col-wise struture
        in a series of bias frames

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs
        slot (str)           Slot in question, i.e., 'S00'
        bias (str)           Method to use for unbiasing
        superbias (str)      Method to use for superbias subtraction
        std (bool)           Plot standard deviation instead of median
        """
        self.safe_update(**kwargs)

        slot = self.config.slot
        bias_files = data['BIAS']
        mask_files = get_mask_files(self, **kwargs)
        superbias_frame = get_superbias_frame(self, mask_files=mask_files, **kwargs)

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

            self.get_ccd_data(butler, ccd, biasstruct_data,
                              slot=slot, bias_type=self.config.bias,
                              std=self.config.std, ifile=ifile, nfiles=len(bias_files),
                              superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key, val in biasstruct_data.items():
            dtables.make_datatable('biasst-%s' % key, val)
        return dtables

    def plot(self, dtables, figs, **kwargs):
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

        @param caller (`Task`)     Task that calls this function
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
        ifile = kwargs.get('ifile', 0)
        nfiles = kwargs.get('nfiles', 1)
        slot = kwargs.get('slot')
        bias_type = kwargs.get('bias_type')
        superbias_frame = kwargs.get('superbias_frame', None)

        amps = get_amp_list(butler, ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(butler, ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(butler, ccd, amp)
            if superbias_frame is not None:
                superbias_im = get_raw_image(butler, superbias_frame, amp)
            else:
                superbias_im = None
            image = unbias_amp(img, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
            frames = get_image_frames_2d(image, regions)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                framekey_row = "row_%s" % key
                framekey_col = "col_%s" % key
                struct = array_struct(frames[region], do_std=kwargs.get('std', False))
                key_str = "biasst_%s_a%02i" % (slot, i)
                if key_str not in data[framekey_row]:
                    data[framekey_row][key_str] = np.ndarray((len(struct['rows']), nfiles))
                if key_str not in data[framekey_col]:
                    data[framekey_col][key_str] = np.ndarray((len(struct['cols']), nfiles))
                data[framekey_row][key_str][:, ifile] = struct['rows']
                data[framekey_col][key_str][:, ifile] = struct['cols']


class SuperbiasStructConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    suffix = EOUtilOptions.clone_param('suffix', default='sbiasst')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')
    stat = EOUtilOptions.clone_param('stat')


class SuperbiasStructTask(BiasStructTask):
    """Class to analyze the overscan bias as a function of row number"""

    ConfigClass = SuperbiasStructConfig
    _DefaultName = "SuperbiasStructTask"
    iteratorClass = BiasAnalysisBySlot

    tablename_format = SLOT_SBIAS_TABLE_FORMATTER
    plotname_format = SLOT_SBIAS_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor"""
        BiasStructTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract the row-wise and col-wise struture  in a superbias frame

        @param butler (`Butler`)   The data butler
        @param data (dict)         Dictionary pointing to the bias and mask files
        @param kwargs
            raft (str)           Raft in question, i.e., 'RTM-004-Dev'
            run_num (str)        Run number, i.e,. '6106D'
            slot (str)           Slot in question, i.e., 'S00'
            superbias (str)      Method to use for superbias subtraction
            outdir (str)         Output directory
            std (bool)           Plot standard deviation instead of median
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        if butler is not None:
            sys.stdout.write("Ignoring butler in superbias_struct.extract")
        if data is not None:
            sys.stdout.write("Ignoring butler in superbias_struct.extract")

        mask_files = get_mask_files(self, **kwargs)
        superbias = get_superbias_frame(self, mask_files=mask_files, **kwargs)

        biasstruct_data = {}

        dim_array_dict = get_dimension_arrays_from_ccd(None, superbias)
        for key, val in dim_array_dict.items():
            biasstruct_data[key] = {key:val}

        BiasStructTask.get_ccd_data(None, superbias, biasstruct_data,
                                    slot=slot, bias_type=None,
                                    std=self.config.std, superbias_frame=None)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key, val in biasstruct_data.items():
            dtables.make_datatable('biasst-%s' % key, val)
        return dtables


EO_TASK_FACTORY.add_task_class('BiasStruct', BiasStructTask)
EO_TASK_FACTORY.add_task_class('SuperbiasStruct', SuperbiasStructTask)
