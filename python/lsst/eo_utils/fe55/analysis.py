"""Functions to analyse fe55 and superbias frames"""

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.data_access import get_data_for_run

from .file_utils import SLOT_FE55_TABLE_FORMATTER,\
    SLOT_FE55_PLOT_FORMATTER


class Fe55AnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
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
    datatype = 'fe55'
    testtypes = ['FE55']

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
        if kwargs.get('teststand', 'ts8') in ['ts8']:
            imagetype = cls.datatype.upper()
        else:
            if kwargs.get('data_source', 'glob') in ['glob']:
                imagetype = 'flat_*_flat'
            else:
                imagetype = 'FE55'

        return get_data_for_run(butler, run_num,
                                testtypes=cls.testtypes,
                                imagetype=imagetype,
                                outkey=cls.datatype.upper(), **kwargs)
