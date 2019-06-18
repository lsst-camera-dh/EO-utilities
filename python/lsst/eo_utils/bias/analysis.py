"""Functions to analyse bias and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from .file_utils import get_bias_files_run,\
    SLOT_BIAS_TABLE_FORMATTER, SLOT_BIAS_PLOT_FORMATTER

from .butler_utils import get_bias_files_butler


class BiasAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')
    nfiles = EOUtilOptions.clone_param('nfiles')


class BiasAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard bias data analysis
    """
    # These can overridden by the sub-class
    ConfigClass = BiasAnalysisConfig
    _DefaultName = "BiasAnalysis"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_BIAS_TABLE_FORMATTER
    plotname_format = SLOT_BIAS_PLOT_FORMATTER

    def get_data(self, butler, run_num, **kwargs):
        """Get a set of bias and mask files out of a folder

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
        kwargs.pop('run', None)

        if butler is None:
            retval = get_bias_files_run(run_num, **kwargs)
        else:
            retval = get_bias_files_butler(butler, run_num, **kwargs)
        if not retval:
            self.log.error("Call to get_data returned no data")
        return retval
