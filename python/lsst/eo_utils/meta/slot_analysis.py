"""Class to analyze stacked bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias import BiasFFTTask, BiasStructTask,\
    CorrelWRTOscanTask, OscanAmpStackTask

from lsst.eo_utils.flat import FlatOverscanTask, BFTask, FlatPairTask

from lsst.eo_utils.qe import QEMedianTask


class SlotAnalysisConfig(MetaConfig):
    """Configuration for SlotAnalysisTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    rafts = EOUtilOptions.clone_param('rafts')
    slots = EOUtilOptions.clone_param('slots')
    plot = EOUtilOptions.clone_param('plot')

SlotAnalysisConfig.add_task('_bias_fft', BiasFFTTask)
SlotAnalysisConfig.add_task('_bias_struct', BiasStructTask)
SlotAnalysisConfig.add_task('_correl_wrt_oscan', CorrelWRTOscanTask)
SlotAnalysisConfig.add_task('_oscan_amp_stack', OscanAmpStackTask)
SlotAnalysisConfig.add_task('_flat_overscan', FlatOverscanTask)
SlotAnalysisConfig.add_task('_bf', BFTask)
SlotAnalysisConfig.add_task('_flat_pair', FlatPairTask)
SlotAnalysisConfig.add_task('_qe_median', QEMedianTask)


class SlotAnalysisTask(MetaTask):
    """Analyze Superbias, Superdark and Superflat frames"""

    ConfigClass = SlotAnalysisConfig
    _DefaultName = "SlotAnalysis"


EO_TASK_FACTORY.add_task_class('SlotAnalysis', SlotAnalysisTask)
