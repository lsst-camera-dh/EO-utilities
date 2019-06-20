"""Class to analyze stacked bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias import SuperbiasFFTTask, SuperbiasStructTask

from lsst.eo_utils.sflat import CTETask, SflatRatioTask

from lsst.eo_utils.qe import QETask


class SlotTableAnalysisConfig(MetaConfig):
    """Configuration for SlotTableAnalysisTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    rafts = EOUtilOptions.clone_param('rafts')
    slots = EOUtilOptions.clone_param('slots')
    plot = EOUtilOptions.clone_param('plot')


SlotTableAnalysisConfig.add_task('_superbias_fft', SuperbiasFFTTask)
SlotTableAnalysisConfig.add_task('_superbias_struct', SuperbiasStructTask)
SlotTableAnalysisConfig.add_task('_cte', CTETask)
SlotTableAnalysisConfig.add_task('_sflat_ratio', SflatRatioTask)
SlotTableAnalysisConfig.add_task('_qe', QETask)


class SlotTableAnalysisTask(MetaTask):
    """Analyze Superbias, Superdark and Superflat frames"""

    ConfigClass = SlotTableAnalysisConfig
    _DefaultName = "SlotTableAnalysis"

EO_TASK_FACTORY.add_task_class('SlotTableAnalysis', SlotTableAnalysisTask)
