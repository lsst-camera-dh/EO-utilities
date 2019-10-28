"""Base classes for tasks to analyze dark and superdark frames"""

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.dark.file_utils import SLOT_DARK_TABLE_FORMATTER, SLOT_DARK_PLOT_FORMATTER,\
    SUPERDARK_FORMATTER, SUPERDARK_STAT_FORMATTER


class DarkAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    nfiles = EOUtilOptions.clone_param('nfiles')


class DarkAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard dark data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = DarkAnalysisConfig
    _DefaultName = "DarkAnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_DARK_TABLE_FORMATTER
    plotname_format = SLOT_DARK_PLOT_FORMATTER
    datatype = 'dark'
    testtypes = ['DARK']

    def get_superdark_file(self, suffix, **kwargs):
        """Get the name of the superdark file for a particular run, raft, ccd...

        Parameters
        ----------
        suffix : `str`
            The filename suffix
        kwargs
            Passed to the file name formatter

        Returns
        -------
        retval : `str`
            The filename
        """
        if self.get_config_param('stat', None) in [DEFAULT_STAT_TYPE, None]:
            formatter = SUPERDARK_FORMATTER
        else:
            formatter = SUPERDARK_STAT_FORMATTER

        return self.get_filename_from_format(formatter, suffix, **kwargs)

    def get_superdark_frame(self, mask_files, **kwargs):
        """Get the superdark frame for a particular run, raft, ccd...

        Parameters
        ----------
        mask_files : `list`
            The files used to build the pixel mask
        types : `str`
            Types of frames to build ['l', 'h', 'ratio']
        kwargs
            Used to override the configuration

        Returns
        -------
        ret_val : `MaskedCCD`
            Superdark frame
        """
        self.safe_update(**kwargs)
        superdark_file = self.get_superdark_file('')
        return self.get_ccd(None, superdark_file, mask_files)
