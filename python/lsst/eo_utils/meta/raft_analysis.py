"""Class to analyze stacked bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.base.eo_results import EOResultsRaftTask

from lsst.eo_utils.bias import OscanAmpStackStatsTask, BiasFFTStatsTask,\
    SuperbiasStatsTask, OscanCorrelTask, CorrelWRTOscanStatsTask

from lsst.eo_utils.dark import DarkCurrentTask

from lsst.eo_utils.fe55 import Fe55GainStatsTask

from lsst.eo_utils.flat import FlatLinearityTask, PTCTask


class RaftAnalysisConfig(MetaConfig):
    """Configuration for RaftAnalysisTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    rafts = EOUtilOptions.clone_param('rafts')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')


RaftAnalysisConfig.add_task('_OscanCorrel', OscanCorrelTask)
RaftAnalysisConfig.add_task('_SuperbiasStats', SuperbiasStatsTask)
RaftAnalysisConfig.add_task('_OscanAmpStackStats', OscanAmpStackStatsTask)
RaftAnalysisConfig.add_task('_BiasFFTStats', BiasFFTStatsTask)
RaftAnalysisConfig.add_task('_DarkCurrent', DarkCurrentTask)
RaftAnalysisConfig.add_task('_Fe55GainStats', Fe55GainStatsTask)
RaftAnalysisConfig.add_task('_FlatLinearity', FlatLinearityTask)
RaftAnalysisConfig.add_task('_PTC', PTCTask)
RaftAnalysisConfig.add_task('_CorrelWRTOscanStats', CorrelWRTOscanStatsTask)
RaftAnalysisConfig.add_task('_EOResultsRaft', EOResultsRaftTask)


class RaftAnalysisTask(MetaTask):
    """Analyze Superbias, Superdark and Superflat frames"""

    ConfigClass = RaftAnalysisConfig
    _DefaultName = "RaftAnalysis"

EO_TASK_FACTORY.add_task_class('RaftAnalysis', RaftAnalysisTask)
