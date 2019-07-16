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
    outdir = EOUtilOptions.clone_param('outdir')
    mask = EOUtilOptions.clone_param('mask')
    skip = EOUtilOptions.clone_param('skip')
    plot = EOUtilOptions.clone_param('plot')
    stats_hist = EOUtilOptions.clone_param('stats_hist')

CalibStackConfig.add_task('_Superbias', SuperbiasTask)
CalibStackConfig.add_task('_Superdark', SuperdarkTask)
CalibStackConfig.add_task('_Superflat', SuperflatTask)


class CalibStackTask(MetaTask):
    """Construct Superbias, Superdark and Superflat frames"""

    ConfigClass = CalibStackConfig
    _DefaultName = "CalibStack"

EO_TASK_FACTORY.add_task_class('CalibStack', CalibStackTask)
