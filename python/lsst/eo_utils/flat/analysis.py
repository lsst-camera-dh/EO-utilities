"""Base classes to analyze flat pairs"""

import lsst.afw.math as afwMath

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.base.file_utils import merge_file_dicts, split_flat_pair_dict

from lsst.eo_utils.base.data_access import get_data_for_run, LOCATION_INFO_DICT

from .file_utils import SLOT_FLAT_TABLE_FORMATTER,\
    SLOT_FLAT_PLOT_FORMATTER


class FlatAnalysisConfig(AnalysisConfig):
    """Configuratioon for flat pair analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    nfiles = EOUtilOptions.clone_param('nfiles')


class FlatAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard flat pair data analysis
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
        self.stat_ctrl.setAndMask(0x7FF)

    @classmethod
    def get_data(cls, butler, run_num, **kwargs):
        """Get a set of flat and mask files for a run

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

        imagetype = LOCATION_INFO_DICT[cls.testtypes[0]].get_imagetype(**kwargs)
        ret_val = {}

        if isinstance(imagetype, list):
            for imgtype in imagetype:
                image_data = get_data_for_run(butler, run_num,
                                              testtypes=cls.testtypes,
                                              imagetype=imgtype,
                                              outkey=imgtype.upper(),
                                              **kwargs)
                ret_val = merge_file_dicts(image_data, ret_val)
        else:
            flat_dict = get_data_for_run(butler, run_num,
                                         testtypes=cls.testtypes,
                                         imagetype=imagetype,
                                         outkey=imagetype.upper(),
                                         **kwargs)
            ret_val = split_flat_pair_dict(flat_dict)
        return ret_val
