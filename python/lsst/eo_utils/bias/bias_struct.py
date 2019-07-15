"""Class to analyze the overscan bias as a function of row number"""

import numpy as np

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES, REGION_LABELS,\
    get_dimension_arrays_from_ccd, get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from .file_utils import SLOT_SBIAS_TABLE_FORMATTER,\
    SLOT_SBIAS_PLOT_FORMATTER

from .analysis import BiasAnalysisTask, BiasAnalysisConfig


class BiasStructConfig(BiasAnalysisConfig):
    """Configuration for BiasVRowTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='biasst')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')


class BiasStructTask(BiasAnalysisTask):
    """Analyze the structure of the bias frames"""

    ConfigClass = BiasStructConfig
    _DefaultName = "BiasStructTask"
    iteratorClass = AnalysisBySlot

    def extract(self, butler, data, **kwargs):
        """Plot the row-wise and col-wise struture
        in a series of bias frames

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

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files=mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(bias_files))

        biasstruct_data = {}

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            ccd = get_ccd_from_id(butler, bias_file, mask_files)
            if ifile == 0:
                dim_array_dict = get_dimension_arrays_from_ccd(ccd)
                for key, val in dim_array_dict.items():
                    biasstruct_data[key] = {key:val}

            self.get_ccd_data(ccd, biasstruct_data,
                              slot=slot, ifile=ifile,
                              nfiles_used=len(bias_files),
                              superbias_frame=superbias_frame)

        self.log_progress("Done!")

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key, val in biasstruct_data.items():
            dtables.make_datatable('biasst-%s' % key, val)
        return dtables

    def plot(self, dtables, figs, **kwargs):
        """Plot the bias structure

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
        """
        for rkey, rlabel in zip(REGION_KEYS, REGION_LABELS):
            for dkey in ['row', 'col']:
                datakey = "biasst-%s_%s" % (dkey, rkey)
                figs.setup_amp_plots_grid(datakey, title="%s, profile by %s" % (rlabel, dkey),
                                          xlabel=dkey, ylabel="ADU")
                figs.plot_xy_amps_from_tabledict(dtables, datakey, datakey,
                                                 x_name="%s_%s" % (dkey, rkey), y_name="biasst")


    def get_ccd_data(self, ccd, data, **kwargs):
        """Get the bias values and update the data dictionary

        Parameters
        ----------
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
        bias_type : `str`
            Method to use to construct bias
        std : `bool`
            Used standard deviation instead of mean
        superbias_frame : `MaskedCCD`
            The superbias frame to subtract away
        """
        nfiles_used = kwargs.get('nfiles_used', 1)
        ifile = kwargs.get('ifile', 0)
        slot = kwargs.get('slot')
        superbias_frame = kwargs.get('superbias_frame', None)

        amps = get_amp_list(ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(ccd, amp)
            if superbias_frame is not None:
                superbias_im = get_raw_image(superbias_frame, amp)
            else:
                superbias_im = None
            image = unbias_amp(img, serial_oscan,
                               bias_type=self.get_config_param('bias', None),
                               superbias_im=superbias_im)
            frames = get_image_frames_2d(image, regions)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                framekey_row = "row_%s" % key
                framekey_col = "col_%s" % key
                struct = array_struct(frames[region], do_std=self.config.std)
                key_str = "biasst_%s_a%02i" % (slot, i)
                if key_str not in data[framekey_row]:
                    data[framekey_row][key_str] = np.ndarray((len(struct['rows']),
                                                              nfiles_used))
                if key_str not in data[framekey_col]:
                    data[framekey_col][key_str] = np.ndarray((len(struct['cols']),
                                                              nfiles_used))
                data[framekey_row][key_str][:, ifile] = struct['rows']
                data[framekey_col][key_str][:, ifile] = struct['cols']


class SuperbiasStructConfig(BiasAnalysisConfig):
    """Configuration for SuperbiasStructTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='sbiasst')
    superbias = EOUtilOptions.clone_param('superbias')
    bias = EOUtilOptions.clone_param('bias')
    mask = EOUtilOptions.clone_param('mask')
    std = EOUtilOptions.clone_param('std')
    stat = EOUtilOptions.clone_param('stat')


class SuperbiasStructTask(BiasStructTask):
    """Analyze the superbias stucture"""

    ConfigClass = SuperbiasStructConfig
    _DefaultName = "SuperbiasStructTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_SBIAS_TABLE_FORMATTER
    plotname_format = SLOT_SBIAS_PLOT_FORMATTER

    def extract(self, butler, data, **kwargs):
        """Extract the row-wise and col-wise struture  in a superbias frame

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

        if butler is not None:
            self.log.warn("Ignoring butler")
        if data is not None:
            self.log.warn("Ignoring data")

        mask_files = self.get_mask_files()
        superbias = self.get_superbias_frame(mask_files=mask_files)

        self.log_info_slot_msg(self.config, "")

        biasstruct_data = {}

        dim_array_dict = get_dimension_arrays_from_ccd(superbias)
        for key, val in dim_array_dict.items():
            biasstruct_data[key] = {key:val}

        self.get_ccd_data(superbias, biasstruct_data,
                          slot=slot, bias_type=None,
                          std=self.config.std, superbias_frame=None)

        self.log_progress("Done!")


        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key, val in biasstruct_data.items():
            dtables.make_datatable('biasst-%s' % key, val)
        return dtables


EO_TASK_FACTORY.add_task_class('BiasStruct', BiasStructTask)
EO_TASK_FACTORY.add_task_class('SuperbiasStruct', SuperbiasStructTask)
