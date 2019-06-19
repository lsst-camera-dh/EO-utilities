"""Class to analyze stacked bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias import OscanAmpStackStatsTask, BiasFFTStatsTask

from lsst.eo_utils.dark import DarkCurrentTask

from lsst.eo_utils.fe55 import Fe55GainStatsTask

from lsst.eo_utils.flat import FlatLinearityTask, PTCTask


class RaftAnalysisConfig(MetaConfig):
    """Configuration for RaftAnalysisTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    rafts = EOUtilOptions.clone_param('rafts')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    plot = EOUtilOptions.clone_param('plot')

RaftAnalysisConfig.add_task('_oscan_amp_stack_stats', OscanAmpStackStatsTask)
RaftAnalysisConfig.add_task('_bias_fft_stats', BiasFFTStatsTask)
RaftAnalysisConfig.add_task('_dark_current', DarkCurrentTask)
#RaftAnalysisConfig.add_task('_fe55_gain_stats', Fe55GainStatsTask)
RaftAnalysisConfig.add_task('_flat_linearity', FlatLinearityTask)
RaftAnalysisConfig.add_task('_ptc', PTCTask)


class RaftAnalysisTask(MetaTask):
    """Analyze Superbias, Superdark and Superflat frames"""

    ConfigClass = RaftAnalysisConfig
    _DefaultName = "RaftAnalysis"

EO_TASK_FACTORY.add_task_class('RaftAnalysis', RaftAnalysisTask)
