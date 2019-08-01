"""Functions to analyse flat and superbias frames"""

import lsst.afw.math as afwMath

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.file_utils import merge_file_dicts, split_flat_pair_dict

from lsst.eo_utils.base.data_access import get_data_for_run

from .file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    SLOT_FLAT_PLOT_FORMATTER


class FlatAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    nfiles = EOUtilOptions.clone_param('nfiles')


class FlatAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard flat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = FlatAnalysisConfig
    _DefaultName = "FlatAnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_FLAT_TABLE_FORMATTER
    plotname_format = SLOT_FLAT_PLOT_FORMATTER
    datatype = 'flat'
    testtypes = ['FLAT']

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)
        self.stat_ctrl = afwMath.StatisticsControl()

    @classmethod
    def get_data(cls, butler, run_num, **kwargs):
        """Get a set of flat and mask files out of a folder

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
        if kwargs.get('data_source', 'glob') in ['glob']:
            flat1_dict = get_data_for_run(butler, run_num,
                                          testtypes=['FLAT'],
                                          imagetype="FLAT1",
                                          outkey='FLAT1',
                                          **kwargs)
            flat2_dict = get_data_for_run(butler, run_num,
                                          testtypes=['FLAT'],
                                          imagetype="FLAT2",
                                          outkey='FLAT2',
                                          **kwargs)
            return merge_file_dicts(flat1_dict, flat2_dict)

        flat_dict = get_data_for_run(butler, run_num,
                                     testtypes=['FLAT'],
                                     imagetype="FLAT",
                                     outkey='FLAT',
                                     **kwargs)
        return split_flat_pair_dict(flat_dict)
