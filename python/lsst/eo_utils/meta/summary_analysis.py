"""Class to analyze stacked bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias import BiasFFTSummaryTask, OscanAmpStackSummaryTask,\
    SuperbiasSummaryTask

from lsst.eo_utils.dark import DarkCurrentSummaryTask

from lsst.eo_utils.fe55 import Fe55GainSummaryTask

from lsst.eo_utils.flat import PTCSummaryTask


class SummaryAnalysisConfig(MetaConfig):
    """Configuration for SummaryAnalysisTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    plot = EOUtilOptions.clone_param('plot')


SummaryAnalysisConfig.add_task('_bias_fft_sum', BiasFFTSummaryTask)
SummaryAnalysisConfig.add_task('_oscan_amp_stack_sum', OscanAmpStackSummaryTask)
SummaryAnalysisConfig.add_task('_superbias_sum', SuperbiasSummaryTask)
SummaryAnalysisConfig.add_task('_dark_current_sum', DarkCurrentSummaryTask)
SummaryAnalysisConfig.add_task('_fe55_gain_sum', Fe55GainSummaryTask)
SummaryAnalysisConfig.add_task('_ptc_sum', PTCSummaryTask)


class SummaryAnalysisTask(MetaTask):
    """Analyze Superbias, Superdark and Superflat frames"""

    ConfigClass = SummaryAnalysisConfig
    _DefaultName = "SummaryAnalysis"

EO_TASK_FACTORY.add_task_class('SummaryAnalysis', SummaryAnalysisTask)
