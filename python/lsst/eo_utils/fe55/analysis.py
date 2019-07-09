"""Functions to analyse fe55 and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.fe55.file_utils import get_fe55_files_run,\
    SLOT_FE55_TABLE_FORMATTER, SLOT_FE55_PLOT_FORMATTER

from lsst.eo_utils.fe55.butler_utils import get_fe55_files_butler


class Fe55AnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')
    nfiles = EOUtilOptions.clone_param('nfiles')


class Fe55AnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard fe55 data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = Fe55AnalysisConfig
    _DefaultName = "Fe55AnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_FE55_TABLE_FORMATTER
    plotname_format = SLOT_FE55_PLOT_FORMATTER

    def get_data(self, butler, run_num, **kwargs):
        """Get a set of fe55 and mask files out of a folder

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        kwargs.pop('run_num', None)
        if butler is None:
            retval = get_fe55_files_run(run_num, **kwargs)
        else:
            retval = get_fe55_files_butler(butler, run_num, **kwargs)
        if not retval:
            self.log.error("Call to get_data returned no data")

        return retval
