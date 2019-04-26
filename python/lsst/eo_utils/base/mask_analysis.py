"""Utilities for offline data analysis of LSST Electrical-Optical testing"""


from lsst.eotest.sensor import add_mask_files


from .iter_utils import AnalysisBySlot

from .analysis import BaseAnalysisConfig, BaseAnalysisTask, EO_TASK_FACTORY

from .config_utils import EOUtilOptions

from .file_utils import makedir_safe, get_mask_files_run,\
    mask_filename, MASKFILENAME_DEFAULTS


def get_mask_data(caller, butler, run_num, **kwargs):
    """Get a set of mask files out of a folder

    @param caller (`Task')     Task we are getting the data for
    @param butler (Bulter)     The data Butler
    @param run_num (str)       The number number we are reading
    @param kwargs:
        mask_types (list)       The types of acquistions we want to include

    @returns (dict) Dictionary mapping slot to file names
    """
    kwargs.pop('run_num', None)
    if butler is None:
        retval = get_mask_files_run(run_num, **kwargs)
    else:
        raise NotImplementedError("Can't get mask files from Butler for %s" % caller)

    return retval



class MaskAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis task over all the slots in a raft"""

    # Function to get the data
    get_data = get_mask_data

    def __init__(self, task):
        """C'tor

        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisBySlot.__init__(self, task)


class MaskAddConfig(BaseAnalysisConfig):
    """Configuration for EO analysis tasks"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    suffix = EOUtilOptions.clone_param('suffix')


class MaskAddTask(BaseAnalysisTask):
    """Simple functor class to tie together standard data analysis
    """
    ConfigClass = MaskAddConfig
    _DefaultName = "MaskAdd"
    iteratorClass = MaskAnalysisBySlot

    def __init__(self, **kwargs):
        """ C'tor

        @param kwargs:    Used to override configruation
        """
        BaseAnalysisTask.__init__(self, **kwargs)


    def __call__(self, butler, slot_data, **kwargs):
        """Make a mask file by or-ing together a set of other mask files

        @param: butler (Bulter)  The data Butler
        @param slot_data (dict)  Dictionary pointing to the mask files
        @param kwargs:           Passed to the `mask_filename` function to get the
                                 output filename
        """
        self.safe_update(**kwargs)

        mask_files = slot_data['MASK']
        if butler is not None:
            print("Ignoring Butler to get mask files")

        mask_kwargs = self.extract_config_vals(MASKFILENAME_DEFAULTS)

        outfile = mask_filename(self, **mask_kwargs)
        makedir_safe(outfile)

        add_mask_files(mask_files, outfile)


EO_TASK_FACTORY.add_task_class('MaskAdd', MaskAddTask)
