"""Functions to iterate over sensor and rafts"""

import sys
import os

from .mpl_utils import init_matplotlib_backend
init_matplotlib_backend()

import matplotlib.pyplot as plt

from lsst.eo_utils.config_utils import setup_parser, EOUtilConfig, make_argstring
import lsst.pipe.base as pipeBase

from .file_utils import get_hardware_type_and_id
from .batch_utils import dispatch_job

ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
ALL_RAFTS = ['R11', 'R12']


class EO_AnalyzeSlotTask(pipeBase.Task):
    """A small class to wrap an analysis function as a pipeline task"""
    ConfigClass = EOUtilConfig
    _DefaultName = "EO_AnalyzeSlot"

    def __init__(self, analysis_func):
        """C'tor

        @param analysis_func (function)  The function that does that actual analysis
        """
        super(EO_AnalyzeSlotTask, self).__init__()
        self.analysis_func = analysis_func

    @pipeBase.timeMethod
    def run(self, raft, run_num, slot, slot_data, **kwargs):
        """Call the analysis function for one sensor

        Parameters
        ----------
        @param raft (str)         The raft idenfier (used for the output file naming)
        @param run_num (str)      The run identifier
        @param slot (str)         The ccd slot (used for the output file naming)
        @param slot_data (dict)   Dictionary with all the files need for analysis
        @param kwargs             Passed along to the analysis function
        """
        self.analysis_func(raft, run_num, slot, slot_data, **kwargs)


class EO_AnalyzeRaftTask(pipeBase.Task):
    """A small class to wrap an analysis function as a pipeline task"""
    ConfigClass = EOUtilConfig
    _DefaultName = "EO_AnalyzeRaft"

    def __init__(self, analysis_func):
        """C'tor

        @param analysis_func (function)  The function that does that actual analysis
        """
        super(EO_AnalyzeRaftTask, self).__init__()
        self.analysis_func = analysis_func

    @pipeBase.timeMethod
    def run(self, raft, run_num, raft_data, **kwargs):
        """Call the analysis function for one raft

        Parameters
        ----------
        @param raft (str)         The raft idenfier (used for the output file naming)
        @param run_num (str)      The run identifier
        @param raft_data (dict)   Dictionary with all the files need for analysis
        @param kwargs             Passed along to the analysis function
        """
        self.analysis_func(raft, run_num, raft_data, **kwargs)



class AnalysisIterator(object):
    """Small class to iterate an analysis, and provied an interface to the batch system"""
    batch_argnames = ['logdir', 'logsuffix', 'bsub_args', 'batch', 'dry_run']
    def __init__(self, task, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        self.task = task
        self.argnames = argnames
        self.argnames += self.batch_argnames

    def call_func(self, run_num, **kwargs):
        """Needs to be implemented by sub-classes"""
        raise NotImplementedError("AnalysisIterator.call_func")

    def run(self):
        """Run the analysis, this task the arguments from the command line using the argparse interface"""
        parser = setup_parser(self.argnames)
        args = parser.parse_args()

        jobname = os.path.basename(sys.argv[0])
        hinfo = get_hardware_type_and_id(args.db, args.run)
        hid = hinfo[1]
        logfile = os.path.join(args.logdir, "%s_%s_%s%s.log" % (hid, args.run,
                                                                jobname.replace('.py', ''), args.logsuffix))

        arg_dict = args.__dict__.copy()
        run_num = arg_dict.pop('run')
        batch = arg_dict.pop('batch')
        arg_dict.pop('logdir')
        arg_dict.pop('logsuffix')

        if batch is None:
            self.call_func(run_num, **arg_dict)
        elif batch == 'slot':
            slots = arg_dict.pop('slots')
            if slots is None:
                slots = ALL_SLOTS
            for slot in slots:
                arg_dict['slots'] = slot
                arg_dict.pop('optstring', None)
                bsub_args = arg_dict.pop('bsub_args')
                arg_dict['optstring'] = make_argstring(arg_dict)
                arg_dict['bsub_args'] = bsub_args
                logfile_slot = logfile.replace('.log', '_%s.log' % slot)
                dispatch_job(jobname, run_num, logfile_slot, **arg_dict)
        else:
            bsub_args = arg_dict.pop('bsub_args')
            arg_dict['optstring'] = make_argstring(arg_dict)
            arg_dict['bsub_args'] = bsub_args
            dispatch_job(jobname, run_num, logfile, **arg_dict)



def iterate_over_slots(task, raft, run_num, data_files, **kwargs):
    """Run a task over a series of slots

    @param task (Task)        The pipeline task
    @param raft (str)         The raft idenfier (used for the output file naming)
    @param run_num (str)      The run identifier
    @param data_files (dict)  Dictionary with all the files need for analysis
    @param kwargs             Passed along to the analysis function
    """

    slot_list = kwargs.get('slots', None)
    if slot_list is None:
        slot_list = ALL_SLOTS

    # If we are doing more that one slot, don't show the plots
    if len(slot_list) > 1:
        plt.ioff()
    else:
        plt.ion()

    for slot in slot_list:
        slot_data = data_files[slot]
        task.run(raft, run_num, slot, slot_data, **kwargs)



def iterate_over_rafts(task, run_num, data_files, **kwargs):
    """Run a task over a series of rafts

    @param task (Task)        The pipeline task
    @param run_num (str)      The run identifier
    @param data_files (dict)  Dictionary with all the files need for analysis
    @param kwargs             Passed along to the analysis function
    """
    raft_list = kwargs.get('rafts', None)
    if raft_list is None:
        raft_list = ALL_RAFTS

    for raft in raft_list:
        raft_data = data_files[raft]
        iterate_over_slots(task, raft, run_num, raft_data, **kwargs)
