"""Class to merge together masks for a single run, raft, slot"""

import sys

from lsst.eotest.sensor import add_mask_files

from .iter_utils import AnalysisBySlot

from .analysis import BaseAnalysisConfig, BaseAnalysisTask

from .factory import EO_TASK_FACTORY

from .config_utils import EOUtilOptions

from .file_utils import makedir_safe, get_mask_files_run,\
    MASK_FORMATTER


class MaskAddConfig(BaseAnalysisConfig):
    """Configuration for MaskAddTask"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix', default='_mask.fits')


class MaskAddTask(BaseAnalysisTask):
    """Merge together masks for a single run, raft, slot
    """
    ConfigClass = MaskAddConfig
    _DefaultName = "MaskAdd"
    iteratorClass = AnalysisBySlot

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs            Used to override configruation
        """
        BaseAnalysisTask.__init__(self, **kwargs)

    def get_data(self, butler, run, **kwargs):
        """Get a set of mask files out of a folder

        @param butler (`Bulter`)   The data Butler
        @param run (str)           The run number we are reading
        @param kwargs:
            mask_types (list)      The types of acquistions we want to include

        @returns (dict) Dictionary mapping slot to file names
        """
        kwargs.pop('run', None)
        if butler is None:
            retval = get_mask_files_run(run, **kwargs)
        else:
            raise NotImplementedError("Can't get mask files from Butler for %s" % self.getName())

        return retval

    def __call__(self, butler, slot_data, **kwargs):
        """Make a mask file by or-ing together a set of other mask files

        @param: butler (Bulter)  The data Butler
        @param slot_data (dict)  Dictionary pointing to the mask files

        @param kwargs            Used to override configruation
        """
        self.safe_update(**kwargs)

        mask_files = slot_data['MASK']
        if butler is not None:
            sys.stdout.write("Ignoring Butler to get mask files\n")

        outfile = self.get_filename_from_format(MASK_FORMATTER, self.config.outsuffix)
        makedir_safe(outfile)

        add_mask_files(mask_files, outfile)


EO_TASK_FACTORY.add_task_class('MaskAdd', MaskAddTask)
