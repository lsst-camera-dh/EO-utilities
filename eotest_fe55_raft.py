import argparse
import os

from lsst.eotest.sensor.spotTask import make_ccd_mosaic
from lsst.pipe.tasks.characterizeImage import CharacterizeImageTask, CharacterizeImageConfig
from lsst.pipe.tasks.calibrate import CalibrateTask, CalibrateConfig
import lsst.meas.extensions.shapeHSM
import lsst.afw.image as afwImage

def make_fe55_catalog(filename, bias_frame):
    
    hsm_plugins = set(["ext_shapeHSM_HsmShapeBj",      # Bernstein & Jarvis 2002
                       "ext_shapeHSM_HsmShapeLinear",  # Hirata & Seljak 2003
                       "ext_shapeHSM_HsmShapeKsb",     # KSB 1995
                       "ext_shapeHSM_HsmShapeRegauss", # Hirata & Seljak 2003
                       "ext_shapeHSM_HsmSourceMoments",# Not PSF corrected; used by all of the above
                       "ext_shapeHSM_HsmPsfMoments"])
    
    ## Combine into a full CCD image mosaic
    image = make_ccd_mosaic(filename, bias_frame)
    exposure = afwImage.ExposureF(image.getBBox())
    exposure.setImage(image)
     
    ## Configure and run CharacterizeImageTask 
    charConfig = CharacterizeImageConfig()
    charConfig.installSimplePsf.fwhm = .05 
    charConfig.doMeasurePsf = False
    charConfig.doApCorr = False 
    charConfig.repair.doCosmicRay = False  
    charConfig.doWrite = False
    charConfig.detection.background.binSize = 10  
    charConfig.detection.minPixels = 1   
    charConfig.measurement.plugins.names |= hsm_plugins

    charTask = CharacterizeImageTask(config=charConfig)
    print("Running CharacterizeImageTask")
    charResult = charTask.characterize(exposure) 

    ## Configure and run CalibrateTask
    calConfig = CalibrateConfig()
    calConfig.doAstrometry = False
    calConfig.doPhotoCal = False
    calConfig.doApCorr = False
    calConfig.doWrite = False
    calConfig.doDeblend = False   
    calConfig.detection.background.binSize = 50
    calConfig.detection.minPixels = 1
    calConfig.measurement.plugins.names |= hsm_plugins

    calTask = CalibrateTask(config= calConfig, icSourceSchema=charResult.sourceCat.schema)    
    print("Running CalibrateTask")
    calResult = calTask.calibrate(charResult.exposure, background=charResult.background,
                            icSourceCat = charResult.sourceCat)
    
    src=calResult.sourceCat
    
    return src

def main(fe55_files, output_dir = './', bias_frame=None):

    for fe55_file in fe55_files:

        src = make_fe55_catalog(fe55_file, bias_frame)
        catalog_filename = os.path.join(output_dir, 
                                        fe55_file.split('/')[-1].replace('.fits','.cat'))
        src.writeFits(catalog_filename)
        print(catalog_filename)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('fe55_files', nargs='+')
    parser.add_argument('--bias', '-b', type=str, default=None)
    parser.add_argument('--output_dir', '-o', type=str, default='./')
    args = parser.parse_args()

    fe55_files = args.fe55_files
    bias_frame = args.bias
    output_dir = args.output_dir

    main(fe55_files, output_dir, bias_frame)
