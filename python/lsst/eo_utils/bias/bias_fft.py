"""Class to analyze the overscan bias as a function of row number"""

import sys

import numpy as np

from scipy import fftpack

from lsst.eo_utils.base.config_utils import STANDARD_SLOT_ARGS

from lsst.eo_utils.base.file_utils import get_mask_files

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.butler_utils import make_file_dict

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    get_readout_frequencies_from_ccd, get_ccd_from_id, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp

from .file_utils import get_superbias_frame,\
    slot_superbias_tablename, slot_superbias_plotname

from .analysis import BiasAnalysisFunc, BiasAnalysisBySlot

DEFAULT_BIAS_TYPE = 'spline'

class bias_fft(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['mask', 'bias', 'superbias', 'std']
    analysisClass = BiasAnalysisBySlot

    def __init__(self):
        """C'tor """
        BiasAnalysisFunc.__init__(self, "biasval", bias_fft.extract, bias_fft.plot)

    @staticmethod
    def extract(butler, slot_data, **kwargs):
        """Extract the bias as function of row

        @param butler (`Butler`)   The data butler
        @param slot_data (dict)    Dictionary pointing to the bias and mask files
        @param kwargs
            slot (str)           Slot in question, i.e., 'S00'
            bias (str)           Method to use for unbiasing

        @returns (TableDict) with the extracted data
        """
        slot = kwargs['slot']
        std = kwargs.get('std', False)
        bias_type = kwargs.get('bias', DEFAULT_BIAS_TYPE)

        bias_files = slot_data['BIAS']
        mask_files = get_mask_files(**kwargs)
        superbias_frame = get_superbias_frame(mask_files=mask_files, **kwargs)

        sys.stdout.write("Working on %s, %i files: " % (slot, len(bias_files)))
        sys.stdout.flush()

        fft_data = {}

        for ifile, bias_file in enumerate(bias_files):
            if ifile % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            ccd = get_ccd_from_id(butler, bias_file, mask_files)
            if ifile == 0:
                freqs_dict = get_readout_frequencies_from_ccd(butler, ccd)
            for key in REGION_KEYS:
                freqs = freqs_dict['freqs_%s' % key]
                nfreqs = len(freqs)
                fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])

            bias_fft.get_ccd_data(butler, ccd, fft_data,
                                  ifile=ifile, nfiles=len(bias_files),
                                  slot=slot, bias_type=bias_type,
                                  std=std, superbias_frame=superbias_frame)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(butler, bias_files))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])

        return dtables


    @staticmethod
    def plot(dtables, figs):
        """Plot the bias as function of row

        @param dtables (`TableDict`)  The data
        @param figs (`FigureDict`)    Object to store the figues
        """
        for key, region in zip(REGION_KEYS, REGION_NAMES):
            datakey = 'biasfft-%s' % key
            figs.setup_amp_plots_grid(datakey, title="FFT of %s region mean by row" % region,
                                      xlabel="Frequency [Hz]", ylabel="Magnitude [ADU]")
            figs.plot_xy_amps_from_tabledict(dtables, datakey, datakey,
                                             x_name='freqs', y_name='fftpow')

    @staticmethod
    def get_ccd_data(butler, ccd, data, **kwargs):

        """Get the fft of the overscan values and update the data dictionary

        @param butler (`Butler`)   The data butler
        @param ccd (`MaskedCCD`)   The ccd we are getting data from
        @param data (dict)         The data we are updatign
        @param kwargs:
            slot  (str)                 The slot number
            ifile (int)                 The file index
            nfiles (int)                Total number of files
            bias_type (str)             Method to use to construct bias
            std (str)                   Do standard deviation instead of mean
            superbias_frame (MaskedCCD) The superbias
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
                if butler is not None:
                    superbias_im = get_raw_image(None, superbias_frame, amp+1)
                else:
                    superbias_im = get_raw_image(None, superbias_frame, amp)
            else:
                superbias_im = None
            image = unbias_amp(im, serial_oscan, bias_type=bias_type, superbias_im=superbias_im)
            frames = get_image_frames_2d(image, regions)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                struct = array_struct(frames[region], do_std=std)
                fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
                nval = len(fftpow)
                fftpow /= nval/2
                key_str = "fftpow_%s_a%02i" % (slot, i)
                if key_str not in data[key]:
                    data[key][key_str] = np.ndarray((int(nval/2), nfiles))
                data[key][key_str][:, ifile] = np.sqrt(fftpow[0:int(nval/2)])



class superbias_fft(BiasAnalysisFunc):
    """Class to analyze the overscan bias as a function of row number"""

    argnames = STANDARD_SLOT_ARGS + ['mask', 'superbias', 'std']
    analysisClass = BiasAnalysisBySlot

    def __init__(self):
        BiasAnalysisFunc.__init__(self, "sbiasfft", self.extract, bias_fft.plot,
                                  tablename_func=slot_superbias_tablename,
                                  plotname_func=slot_superbias_plotname)

    @staticmethod
    def extract(butler, slot_data, **kwargs):
        """Extract the FFTs of the row-wise and col-wise struture
        in a superbias frame

        @param butler (Butler)   The data butler
        @param slot_data (dict)  Dictionary pointing to the bias and mask files
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
            sys.stdout.write("Ignoring butler in extract_superbias_fft_slot")
        if slot_data is not None:
            sys.stdout.write("Ignoring raft_data in extract_superbias_fft_raft")

        mask_files = get_mask_files(**kwargs)
        superbias = get_superbias_frame(mask_files=mask_files, **kwargs)

        fft_data = {}

        freqs_dict = get_readout_frequencies_from_ccd(None, superbias)
        for key in REGION_KEYS:
            freqs = freqs_dict['freqs_%s' % key]
            nfreqs = len(freqs)
            fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])

        bias_fft.get_ccd_data(None, superbias, fft_data,
                              slot=slot, bias_type=kwargs.get('superbias'),
                              std=std, superbias_frame=None)

        sys.stdout.write("!\n")
        sys.stdout.flush()

        dtables = TableDict()
        dtables.make_datatable('files', make_file_dict(None, [slot]))
        for key in REGION_KEYS:
            dtables.make_datatable('biasfft-%s' % key, fft_data[key])
        return dtables
