
import math
import numpy as np

from astropy.table import Table

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

__all__ = ["BiasFFTTask", "BiasFFTTaskConfig"]


class BiasFFTConnections(pipeBase.PipelineTaskConnections,
                        dimensions=("instrument", "exposure", "detector")):
    inputExp = cT.Input(
        name="raw",
        doc="Extract FFT from Bias Frames.",
        storageClass="Exposure",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_s = cT.Output(
        name="biasFFT_serial",
        doc="Table of FFT measurements in serial direction",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasFFT_p = cT.Output(
        name="biasFFT_parallel",
        doc="Table of FFT measurements in parallel direction",
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
        outputBiasFFT_s : `astropy.Table`
            Table of FFTs in serial direction
            
        outputBiasFFT_p : `astropy.Table`
            Table of FFTs in parallel direction
        """
        
        outputBiasFFT_s = Table(dict(col=np.linspace(0, 50., 51)))
        outputBiasFFT_p = Table(dict(row=np.linspace(0, 25., 26)))

        ccd = self.get_ccd(butler, inputExp
        freqs_dict = self.get_readout_freqs_from_ccd(ccd)
        
        fft_data = {}
        for key in REGION_KEYS:
            freqs = freqs_dict['freqs_%s' % key]
            freqs_col = freqs_dict['freqs_%s_col' % key]
            nfreqs = len(freqs)
            nfreqs_col = len(freqs_col)
            if key not in fft_data:
                fft_data[key] = dict(freqs=freqs[0:int(nfreqs/2)])
                fft_data["%s_col" % key] = dict(freqs=freqs_col[0:int(nfreqs_col/2)])

        self._get_ccd_data(ccd, fft_data, master_bias=master_bias)

        print(outputBiasFFT_s)
        
        return pipeBase.Struct(
            outputBiasFFT_s=fft_data['
            outputBiasFFT_p=outputBiasFFT_p,
        )


    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        """
        """
        inputData = butlerQC.get(inputRefs)

        results = self.run(**inputData)
        butlerQC.put(results, outputRefs) 
