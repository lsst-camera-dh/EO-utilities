"""Tasks to analyse sflat and superbias frames"""

import lsst.afw.math as afwMath

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.sflat.file_utils import SLOT_SFLAT_TABLE_FORMATTER,\
    SLOT_SFLAT_PLOT_FORMATTER,\
    SUPERFLAT_FORMATTER, SUPERFLAT_STAT_FORMATTER


class SflatAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    nfiles = EOUtilOptions.clone_param('nfiles')


class SflatAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard sflat data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = SflatAnalysisConfig
    _DefaultName = "SflatAnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_SFLAT_TABLE_FORMATTER
    plotname_format = SLOT_SFLAT_PLOT_FORMATTER
    datatype = 'sflat'
    testtypes = ['SFLAT']

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

    def get_superflat_file(self, suffix, **kwargs):
        """Get the name of the superbias file for a particular run, raft, ccd...

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
            formatter = SUPERFLAT_FORMATTER
        else:
            formatter = SUPERFLAT_STAT_FORMATTER

        return self.get_filename_from_format(formatter, suffix, **kwargs)

    def get_superflat_frames(self, mask_files, types=None, **kwargs):
        """Get the superbias frame for a particular run, raft, ccd...

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
        o_dict : `dict`
            Dictionary of superflat frames, keyed by type
        """
        self.safe_update(**kwargs)

        if types is None:
            types = ['l', 'h', 'r']

        o_dict = {key:self.get_ccd(None, self.get_superflat_file('_%s.fits' % key), mask_files)
                  for key in types}
        return o_dict
