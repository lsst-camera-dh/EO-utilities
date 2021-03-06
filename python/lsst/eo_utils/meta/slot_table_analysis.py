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
    skip = EOUtilOptions.clone_param('skip')


SlotTableAnalysisConfig.add_task('_SuperbiasFFT', SuperbiasFFTTask)
SlotTableAnalysisConfig.add_task('_SuperbiasStruct', SuperbiasStructTask)
SlotTableAnalysisConfig.add_task('_CTE', CTETask)
SlotTableAnalysisConfig.add_task('_SflatRatio', SflatRatioTask)
SlotTableAnalysisConfig.add_task('_QE', QETask)


class SlotTableAnalysisTask(MetaTask):
    """Chain together all the slot-based table analyses"""

    ConfigClass = SlotTableAnalysisConfig
    _DefaultName = "SlotTableAnalysis"

EO_TASK_FACTORY.add_task_class('SlotTableAnalysis', SlotTableAnalysisTask)
