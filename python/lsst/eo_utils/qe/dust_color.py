"""Class to analyze the FFT of the bias frames"""

import sys

from lsst.eo_utils.base.defaults import ALL_SLOTS

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.data_utils import TableDict, construct_bbox_dict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_ccd_from_id, get_amp_list,\
    get_exposure_time, get_mondiode_val, get_mono_wl,\
    get_geom_regions, get_raw_image, unbias_amp

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.sflat.file_utils import RAFT_SFLAT_TABLE_FORMATTER

from lsst.eo_utils.qe.file_utils import SLOT_QE_TABLE_FORMATTER,\
    RAFT_QE_TABLE_FORMATTER, RAFT_QE_PLOT_FORMATTER

from lsst.eo_utils.qe.analysis import QeAnalysisConfig, QeAnalysisTask


class DustColorConfig(QeAnalysisConfig):
    """Configuration for DustColorTask"""
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='dust_color')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    mask = EOUtilOptions.clone_param('mask')


class DustColorTask(QeAnalysisTask):
    """Analyze some qe data"""

    ConfigClass = DustColorConfig
    _DefaultName = "DustColorTask"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        QeAnalysisTask.__init__(self, **kwargs)

    def extract(self, butler, data, **kwargs):
        """Extract data

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
            Output data tables
        """
        self.safe_update(**kwargs)

        slot = self.config.slot

        qe_files = data['LAMBDA']

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(qe_files))

        sflat_table_file = self.get_filename_from_format(RAFT_SFLAT_TABLE_FORMATTER, "sflat.fits")
        print(sflat_table_file)

        sflat_tables = TableDict(sflat_table_file)
        bbox_dict = construct_bbox_dict(sflat_tables['defects'])
        slot_bbox_dict = bbox_dict[slot]        

        # This is a dictionary of dictionaries to store all the
        # data you extract from the qe_files
        data_dict = dict(WL=[], EXPTIME=[], MONDIODE=[])

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        for ifile, qe_file in enumerate(qe_files):
            if ifile % 10 == 0:
                self.log_progress("  %i" % ifile)

            ccd = get_ccd_from_id(butler, qe_file, mask_files)

            data_dict['WL'].append(get_mono_wl(butler, ccd))
            data_dict['EXPTIME'].append(get_exposure_time(butler, ccd))
            data_dict['MONDIODE'].append(get_mondiode_val(butler, ccd))

            amps = get_amp_list(butler, ccd)
            for i, amp in enumerate(amps):

                bbox_list = slot_bbox_dict[i]
                regions = get_geom_regions(butler, ccd, amp)
                serial_oscan = regions['serial_overscan']
                imaging = regions['imaging']

                img = get_raw_image(butler, ccd, amp)
                if superbias_frame is not None:
                    if butler is not None:
                        superbias_im = get_raw_image(None, superbias_frame, amp+1)
                    else:
                        superbias_im = get_raw_image(None, superbias_frame, amp)
                else:
                    superbias_im = None

                image = unbias_amp(img, serial_oscan, bias_type=self.config.bias,
                                   superbias_im=superbias_im, region=imaging)

                max_bbox = min(len(bbox_list), 10)
                for bbox in bbox_list[0:max_bbox]:
                    try:
                        cutout = image[bbox]
                    except:
                        print ("cutout failed", slot, amp, bbox)
                    print(ifile, bbox, cutout)


        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, qe_files))
        dtables.make_datatable('dusk_color', data_dict)

        return dtables


    def plot(self, dtables, figs, **kwargs):
        """Make plots 

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

        # Analysis goes here.
        # you should use the data in dtables to make a bunch of figures in figs



EO_TASK_FACTORY.add_task_class('DustColor', DustColorTask)
