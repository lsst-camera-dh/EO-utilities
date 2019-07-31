"""Tasks to analyse qe (Quantum efficiency) runs"""

import lsst.afw.math as afwMath

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.file_utils import merge_file_dicts, PD_CALIB_FORMATTER

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.data_access import get_data_for_run

from lsst.eo_utils.qe.file_utils import SLOT_QE_TABLE_FORMATTER,\
    SLOT_QE_PLOT_FORMATTER


class QeAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
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
    datatype = 'lambda'

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

    @classmethod
    def get_data(cls, butler, run_num, **kwargs):
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
        kwargs.pop('run', None)
        lambda_dict = get_data_for_run(butler, run_num,
                                       testtypes=['LAMBDA'],
                                       imagetype='flat',
                                       outkey='LAMBDA', **kwargs)
        bias_dict = get_data_for_run(butler, run_num,
                                     testtypes=['LAMBDA'],
                                     imagetype='bias',
                                     outkey='BIAS', **kwargs)
        return merge_file_dicts(lambda_dict, bias_dict)
