"""Functions to analyse sflat and superbias frames"""

import sys

from lsst.eo_utils.base import mpl_utils

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_ccd_from_id

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.sflat.file_utils import get_sflat_files_run,\
    SLOT_SFLAT_TABLE_FORMATTER, SLOT_SFLAT_PLOT_FORMATTER,\
    SUPERFLAT_FORMATTER, SUPERFLAT_STAT_FORMATTER

from lsst.eo_utils.sflat.butler_utils import get_sflat_files_butler

mpl_utils.set_plt_ioff()



class SflatAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')
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

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        AnalysisTask.__init__(self, **kwargs)

    def get_superflat_file(self, suffix, **kwargs):
        """Get the name of the superbias file for a particular run, raft, ccd...

        @param kwargs              Used to override default configuration
        @returns (str)             The filename
        """
        if self.get_config_param('stat', None) in [DEFAULT_STAT_TYPE, None]:
            formatter = SUPERFLAT_FORMATTER
        else:
            formatter = SUPERFLAT_STAT_FORMATTER

        return self.get_filename_from_format(formatter, suffix, **kwargs)

    def get_superflat_frames(self, mask_files, types=None, **kwargs):
        """Get the superbias frame for a particular run, raft, ccd...

        @param types (list)         Types of frames ['l', 'h', 'ratio']

        @returns (`dict`)           The superbias frame
        """
        self.safe_update(**kwargs)

        if types is None:
            types = ['l', 'h', 'ratio']
        superflat_file = self.get_superflat_file('').replace('.fits', '')

        o_dict = {key:get_ccd_from_id(None, superflat_file + '_%s.fits' % key, mask_files)
                  for key in types}
        return o_dict

    def get_data(self, butler, run_num, **kwargs):
        """Get a set of sflat and mask files out of a folder

        @param butler (`Bulter`)    The data Butler
        @param run_num (str)        The run number we are reading
        @param kwargs:
           acq_types (list)  The types of acquistions we want to include

        @returns (dict) Dictionary mapping slot to file names
        """
        kwargs.pop('run_num', None)

        if butler is None:
            retval = get_sflat_files_run(run_num, **kwargs)
        else:
            retval = get_sflat_files_butler(butler, run_num, **kwargs)
        if not retval:
            sys.stdout.write("Warning, call to get_data for %s returned no data" % self.getName())
        return retval

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class"""
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
