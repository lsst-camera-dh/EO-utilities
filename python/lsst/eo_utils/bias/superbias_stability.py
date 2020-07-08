"""Class to construct superbias frames"""

from lsst.eo_utils.base.iter_utils import SummaryAnalysisBySlotIterator

from lsst.eo_utils.base.factory import EO_TASK_FACTORY

from lsst.eo_utils.bias.superbias import SuperbiasConfig,\
    SuperbiasTask

class SuperbiasStabilityConfig(SuperbiasConfig):
    """Configuration for SuperbiasStabilityTask"""


class SuperbiasStabilityTask(SuperbiasTask):
    """Construct superbias frames"""

    ConfigClass = SuperbiasStabilityConfig
    _DefaultName = "SuperbiasStabilityTask"
    iteratorClass = SummaryAnalysisBySlotIterator

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        SuperbiasTask.__init__(self, **kwargs)

    @staticmethod
    def get_input_files(data):
        """Get the input files
        This is useful to specialize sub-classes that do slightly different things

        Parameters
        ----------
        data : `dict`
            Dictionary (or other structure) contain the input data

        Returns
        -------
        """
        return data


EO_TASK_FACTORY.add_task_class('SuperbiasStability', SuperbiasStabilityTask)
