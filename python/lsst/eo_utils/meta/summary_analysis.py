"""Class to analyze stacked bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.base.eo_results import EOResultsSummaryTask

from lsst.eo_utils.bias import BiasFFTSummaryTask, OscanAmpStackSummaryTask,\
    SuperbiasSummaryTask, CorrelWRTOscanSummaryTask

from lsst.eo_utils.dark import DarkCurrentSummaryTask

from lsst.eo_utils.fe55 import Fe55GainSummaryTask

from lsst.eo_utils.flat import PTCSummaryTask


class SummaryAnalysisConfig(MetaConfig):
    """Configuration for SummaryAnalysisTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    plot = EOUtilOptions.clone_param('plot')
    skip = EOUtilOptions.clone_param('skip')


SummaryAnalysisConfig.add_task('_BiasFFTSummary', BiasFFTSummaryTask)
SummaryAnalysisConfig.add_task('_OscanAmpStackSummary', OscanAmpStackSummaryTask)
SummaryAnalysisConfig.add_task('_SuperbiasSummary', SuperbiasSummaryTask)
SummaryAnalysisConfig.add_task('_DarkCurrentSummary', DarkCurrentSummaryTask)
SummaryAnalysisConfig.add_task('_Fe55GainSummary', Fe55GainSummaryTask)
SummaryAnalysisConfig.add_task('_PTCSummary', PTCSummaryTask)
SummaryAnalysisConfig.add_task('_EOResultsSummary', EOResultsSummaryTask)
SummaryAnalysisConfig.add_task('_CorrelWRTOscanSummary', CorrelWRTOscanSummaryTask)


class SummaryAnalysisTask(MetaTask):
    """Analyze Superbias, Superdark and Superflat frames"""

    ConfigClass = SummaryAnalysisConfig
    _DefaultName = "SummaryAnalysis"

EO_TASK_FACTORY.add_task_class('SummaryAnalysis', SummaryAnalysisTask)
