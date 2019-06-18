"""Tasks to analyse qe (Quantum efficiency) runs"""

import lsst.afw.math as afwMath

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.file_utils import PD_CALIB_FORMATTER

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.qe.file_utils import get_qe_files_run,\
    SLOT_QE_TABLE_FORMATTER, SLOT_QE_PLOT_FORMATTER

from lsst.eo_utils.qe.butler_utils import get_qe_files_butler


class QeAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')
    nfiles = EOUtilOptions.clone_param('nfiles')


class QeAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard qe data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = QeAnalysisConfig
    _DefaultName = "QeAnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_QE_TABLE_FORMATTER
    plotname_format = SLOT_QE_PLOT_FORMATTER

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)
        self.stat_ctrl = afwMath.StatisticsControl()

    def get_pd_calib_file(self, **kwargs):
        """Get the name of the pd_calib for a particular run, raft...

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The filename
        """
        return self.get_filename_from_format(PD_CALIB_FORMATTER, '.dat', **kwargs)

    def get_data(self, butler, run_num, **kwargs):
        """Get a set of qe and mask files out of a folder

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
            retval = get_qe_files_run(run_num, **kwargs)
        else:
            retval = get_qe_files_butler(butler, run_num, **kwargs)
        if not retval:
            self.log.error("Call to get_data returned no data")
        return retval
