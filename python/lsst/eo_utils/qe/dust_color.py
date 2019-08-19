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

import numpy as np

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
        lams = []
        for file in qe_files:
            lam = file.split('flat_')[1].split('_')[0]
            lams.append(lam)

        mask_files = self.get_mask_files()
        superbias_frame = self.get_superbias_frame(mask_files)

        self.log_info_slot_msg(self.config, "%i files" % len(qe_files))

        sflat_table_file = self.get_filename_from_format(RAFT_SFLAT_TABLE_FORMATTER, "sflat.fits")

        sflat_tables = TableDict(sflat_table_file)
        bbox_dict = construct_bbox_dict(sflat_tables['defects'])
        slot_bbox_dict = bbox_dict[slot]

        # This is a dictionary of dictionaries to store all the
        # data you extract from the qe_files
        data_dict = dict(SLOT=[], AMP=[], XCORNER=[], YCORNER=[], XSIZE=[], YSIZE=[])
        for lam in lams:
            data_dict['FLUX_' + lam] = []
            data_dict['MED_' + lam] = []

        temp_list = []

        # Analysis goes here, you should fill data_dict with data extracted
        # by the analysis
        #
        # For this slot, loop over qe files, loop over amplifiers, loop over dust spots in that amplifier,
        #  record the flux and median for each dust spot
        # Then loop over dust spots CCDs, amplifiers, and QE files to accumulate the output dictionary
        ccd = get_ccd_from_id(butler, qe_files[0], mask_files)
        amps = get_amp_list(ccd)
        spot = 0
        for ifile, qe_file in enumerate(qe_files):
            lam = qe_file.split('flat_')[1].split('_')[0]
            #for i, amp in enumerate(amps):
            for i, amp in enumerate(slot_bbox_dict.keys()):
                bbox_list = slot_bbox_dict[amp]
                
                if len(bbox_list) > 100:
                    self.log.warn("Skipping slot:amp %s:%i with %i defects" % (slot, amp, len(bbox_list)))
                    continue

                ccd = get_ccd_from_id(butler, qe_file, mask_files)
                regions = get_geom_regions(ccd, amp)
                serial_oscan = regions['serial_overscan']
                imaging = regions['imaging']
                img = get_raw_image(ccd, amp + 1)
                if superbias_frame is not None:
                    if butler is not None:
                        superbias_im = get_raw_image(superbias_frame, amp + 1)
                    else:
                        superbias_im = get_raw_image(superbias_frame, amp + 1) 
                else:
                    superbias_im = None

                image = unbias_amp(img, serial_oscan, bias_type=self.config.bias,
                                   superbias_im=superbias_im, region=imaging)
                for bbox in bbox_list:
                    if ifile == 0:
                        data_dict['SLOT'].append(slot)
                        #data_dict['LAM'].append(lam)
                        data_dict['AMP'].append(amp)
                        data_dict['XCORNER'].append(bbox.getBeginX())
                        data_dict['YCORNER'].append(bbox.getBeginY())
                        data_dict['XSIZE'].append(bbox.getWidth())
                        data_dict['YSIZE'].append(bbox.getHeight())

                    try:
                        cutout = image[bbox]
                    except:
                        pass
                    # Here evaluate the 'flux' of the feature, relative to the median
                    # value of the amplifier image.  May also want to assemble bounding
                    # box corners into a ds9 region file, CCD by CCD
                    med = np.median(image.array)
                    flux = np.sum(cutout.array) - bbox.getWidth()*bbox.getHeight()*med
                    spot += 1
                    #temp_dict[spot].append((lam, flux, med))
                    temp_list.append((lam, flux, med))

        for i in range(len(temp_list)):
            #data_dict['SLOT'].append(temp_dict['SLOT'][i])
            #data_dict['AMP'].append(temp_dict['AMP'][i])
            #lam = temp_dict['LAM'][i]
            lam, flux, med = temp_list[i]
            data_dict['FLUX_' + lam].append(flux)  #temp_dict['FLUX'][i])
            data_dict['MED_' + lam].append(med)  #np.median(image.array))


        sys.stdout.write("!\n")
        sys.stdout.flush()
        for key in data_dict.keys():
            print(key, len(data_dict[key]))

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, qe_files))
        #dtables.make_datatable('dust_color', data_dict)
        dtables.make_datatable('dust_color_hack', data_dict)

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
