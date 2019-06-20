"""Class to stack bias, dark and flat frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.pipeline import MetaConfig, MetaTask

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias import SuperbiasTask

from lsst.eo_utils.dark import SuperdarkTask

from lsst.eo_utils.sflat import SuperflatTask


class CalibStackConfig(MetaConfig):
    """Configuration for CalibStackTask"""
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')
    rafts = EOUtilOptions.clone_param('rafts')
    slots = EOUtilOptions.clone_param('slots')
    mask = EOUtilOptions.clone_param('mask')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')

CalibStackConfig.add_task('_superbias', SuperbiasTask)
CalibStackConfig.add_task('_superdark', SuperdarkTask)
CalibStackConfig.add_task('_superflat', SuperflatTask)


class CalibStackTask(MetaTask):
    """Construct Superbias, Superdark and Superflat frames"""

    ConfigClass = CalibStackConfig
    _DefaultName = "CalibStack"

EO_TASK_FACTORY.add_task_class('CalibStack', CalibStackTask)
