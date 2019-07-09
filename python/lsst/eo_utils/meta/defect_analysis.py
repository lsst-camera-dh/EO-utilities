"""Class to analyze stacked bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias import SuperbiasRaftTask

from lsst.eo_utils.dark import SuperdarkRaftTask

from lsst.eo_utils.sflat import SuperflatRaftTask

from lsst.eo_utils.ppump import TrapTask


class DefectAnalysisConfig(MetaConfig):
    """Configuration for DefectAnalysisTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    rafts = EOUtilOptions.clone_param('rafts')
    slots = EOUtilOptions.clone_param('slots')
    bias = EOUtilOptions.clone_param('bias')
    superbias = EOUtilOptions.clone_param('superbias')
    plot = EOUtilOptions.clone_param('plot')
    mosaic = EOUtilOptions.clone_param('mosaic')

DefectAnalysisConfig.add_task('_SuperbiasRaft', SuperbiasRaftTask)
DefectAnalysisConfig.add_task('_SuperdarkRaft', SuperdarkRaftTask)
DefectAnalysisConfig.add_task('_SuperflatRaft', SuperflatRaftTask)
DefectAnalysisConfig.add_task('_Trap', TrapTask)

class DefectAnalysisTask(MetaTask):
    """Analyze Superbias, Superdark and Superflat frames"""

    ConfigClass = DefectAnalysisConfig
    _DefaultName = "DefectAnalysis"


EO_TASK_FACTORY.add_task_class('DefectAnalysis', DefectAnalysisTask)
