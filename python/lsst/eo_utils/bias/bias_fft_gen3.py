import math
import numpy as np

from astropy.table import Table

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from lsst.eo_utils.base.image_utils import REGION_KEYS, REGION_NAMES,\
    raw_amp_image, get_readout_freqs_from_ccd, get_raw_image,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp,\
    get_amp_offset

__all__ = ["BiasFFTTask", "BiasFFTTaskConfig"]


class BiasFFTConnections(pipeBase.PipelineTaskConnections,
                        dimensions=("instrument", "exposure", "detector")):
    inputExp = cT.Input(
        name="raw",
        doc="Extract FFT from Bias Frames.",
        storageClass="Exposure",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_s_row = cT.Output(
        name="biasFFT_serial_row",
        doc="Table of row-wise FFT measurements in serial overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_p_row = cT.Output(
        name="biasFFT_parallel_row",
        doc="Table of row-wise FFT measurements in parallel overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_i_row = cT.Output(
        name="biasFFT_image_row",
        doc="Table of row-wise FFT measurements in image overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_s_col = cT.Output(
        name="biasFFT_serial_col",
        doc="Table of col-wise FFT measurements in serial overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_p_col = cT.Output(
        name="biasFFT_parallel_col",
        doc="Table of col-wise FFT measurements in parallel overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_i_col = cT.Output(
        name="biasFFT_image_col",
        doc="Table of col-wise FFT measurements in image overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )







class BiasFFTTaskConfig(pipeBase.PipelineTaskConfig,
                        pipelineConnections=BiasFFTConnections):
    pass


class BiasFFTTask(pipeBase.PipelineTask,
                  pipeBase.CmdLineTask):
    """Combine pre-processed dark frames into a proposed master calibration.

    """
    ConfigClass = BiasFFTTaskConfig
    _DefaultName = "biasFFT"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, inputExp):
        """Extract FFT from a bias frame.

        Parameters
        ----------
        inputExp : `lsst.afw.image.Exposure`
            Pre-processed dark frame data to combine.

        Returns
        -------
        """
        # Use MaskedCCD class by default
        data_kw = {'masked_ccd':True}
        ccd = get_ccd_from_id(butler, inputExp, [], **kwargs)
        freqs_dict = get_readout_freqs_from_ccd(ccd)

        fft_data = {}
        for key in REGION_KEYS:
            out_name_row = "outputBiasFFT_%i_row" % key
            out_name_col = "outputBiasFFT_%i_col" % key
            freqs_row = freqs_dict['freqs_%s_row' % key]
            freqs_col = freqs_dict['freqs_%s_col' % key]
            nfreqs_row = len(freqs_row)
            nfreqs_col = len(freqs_col)
            fft_data[out_name_row] = dict(freqs=freqs[0:int(nfreqs/2)])
            fft_data[out_name_col] = dict(freqs=freqs_col[0:int(nfreqs_col/2)])

        self._get_ccd_data(ccd, fft_data, bias_type=None)

        return pipeBase.Struct(**fft_data)


    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        """
        """
        inputData = butlerQC.get(inputRefs)

        results = self.run(**inputData)
        butlerQC.put(results, outputRefs)



    @staticmethod
    def get_ccd_data(ccd, data, **kwargs):
        """Get the fft of the overscan values and update the data dictionary

        Parameters
        ----------
        ccd : `MaskedCCD`
            The ccd we are getting data from
        data : `dict`
            The data we are updating

        Keywords
        --------
        bias_type : `str`
            Method to use to construct bias
        std : `bool`
            Used standard deviation instead of mean
        """
        bias_type = kwargs.get('bias_type', None)
        std = kwargs.get('bias_type', False)

        amps = get_amp_list(ccd)

        for i, amp in enumerate(amps):
            regions = get_geom_regions(ccd, amp)
            serial_oscan = regions['serial_overscan']
            img = get_raw_image(ccd, amp)
            image = unbias_amp(img, serial_oscan,
                               bias_type=bias_type)
            frames = get_image_frames_2d(image, regions)
            key_str = "fftpow_a%02i" % (i)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                key_row = "outputBiasFFT_%i_row" % key
                key_col = "outputBiasFFT_%i_col" % key

                struct = array_struct(frames[region], do_std=std)
                fftpow = np.abs(fftpack.fft(struct['rows']-struct['rows'].mean()))
                nval = len(fftpow)
                fftpow /= nval/2
                data[key_row][key_str] = np.sqrt(fftpow[0:int(nval/2)])

                fft_by_col = []
                for row_data in frames[region]:
                    fftpow_row = np.abs(fftpack.fft(row_data-row_data.mean()))
                    nvals = len(fftpow_row)
                    fftpow_row /= nvals/2
                    fft_by_col.append(fftpow_row[0:int(nvals/2)])
                data[key_col][key_str] = np.sqrt(np.vstack(fft_by_col)).mean(axis=0)
