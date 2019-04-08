"""Tools to iterate analyzes functions over sensor and rafts"""

import sys
import os


import lsst.pipe.base as pipeBase

from .config_utils import setup_parser, EOUtilConfig, make_argstring, get_config_values
from .file_utils import get_hardware_type_and_id
from .butler_utils import getButler, get_hardware_info

from .batch_utils import dispatch_job

# These should be taken from somewhere, not hardcoded here
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
    def run(self, butler, slot_data, **kwargs):
        """Call the analysis function for one sensor

        @param butler (Butler)    The data butler
        @param slot_data (dict)   Dictionary with all the files need for analysis
        @param kwargs             Passed along to the analysis function
        """
        self.analysis_func(butler, slot_data, **kwargs)


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
    def run(self, butler, raft_data, **kwargs):
        """Call the analysis function for one raft

        @param butler (Butler)    The data butler
        @param raft_data (dict)   Dictionary with all the files need for analysis
        @param kwargs             Passed along to the analysis function
        """
        self.analysis_func(butler, raft_data, **kwargs)



class AnalysisIterator:
    """Small class to iterate an analysis, and provied an interface to the batch system"""

    # These are arguement that control batch job submission
    batch_argnames = ['logdir', 'logsuffix', 'bsub_args', 'batch', 'dry_run']

    def __init__(self, task, data_func, argnames):
        """C'tor

        @param task (Task)              The task that does the actual analysis for one CCD
        @param data_func (function)     Function that gets the data to analyze
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        self.task = task
        self.data_func = data_func
        if argnames is None:
            self.argnames = []
        else:
            self.argnames = argnames
        self.argnames += self.batch_argnames

    def call_func(self, run_num, **kwargs):
        """Needs to be implemented by sub-classes"""
        raise NotImplementedError("AnalysisIterator.call_func")

    @staticmethod
    def get_hardware(butler, run_num):
        """return the hardware type and hardware id for a given run

        @param: bulter (`Bulter`)  The data Butler
        @param run_num(str)        The number number we are reading

        @returns (tuple)
            htype (str) The hardware type, either
                        'LCA-10134' (aka full camera) or
                        'LCA-11021' (single raft)
            hid (str) The hardware id, e.g., RMT-004
        """
        if butler is None:
            retval = get_hardware_type_and_id(run_num)
        else:
            retval = get_hardware_info(butler, run_num)
        return retval

    @staticmethod
    def get_butler(butler_repo, **kwargs):
        """Return a data Butler

        @param: bulter_repo (str)  Key specifying the data repo
        @param kwargs (dict)       Passed to the ctor
        
        @returns (`Butler`)        The requested data Butler
        """
        return getButler(butler_repo, **kwargs)

    def get_data(self, butler, run_num, **kwargs):
        """Call the function to get the data

        @param: bulter (`Butler`)    The data Butler
        @param run_num (str)         The run identifier
        @param kwargs (dict)         Passed to the data function
        """
        return self.data_func(butler, run_num, **kwargs)


    def run(self, **kwargs):
        """Run the analysis over all of the requested objects.
        
        By default this takes the arguments from the command line 
        and overrides those with any kwargs that have been provided.

        If interactive==True then it will not use the command line
        arguments.

        If batch is not None then it will send the jobs the the batch.
        """
        interactive = kwargs.get('interactive', False)

        if interactive:
            arg_dict = get_config_values(self.argnames, **kwargs)
            jobname = None
        else:
            jobname = os.path.basename(sys.argv[0])
            parser = setup_parser(self.argnames)
            args = parser.parse_args()
            arg_dict = args.__dict__.copy()
            arg_dict.update(**kwargs)

        run_num = arg_dict.pop('run')
        batch = arg_dict.pop('batch')
        logdir = arg_dict.pop('logdir')
        logsuffix = arg_dict.pop('logsuffix')
        butler_repo = arg_dict.get('butler_repo', None)

        if butler_repo is None:
            butler = None
            hinfo = get_hardware_type_and_id(run_num)
        else:
            butler = self.get_butler(butler_repo)
            hinfo = get_hardware_info(butler, run_num)

        hid = hinfo[1]
        if interactive:
            logfile = None
        else:
            logfile = os.path.join(logdir, "%s_%s_%s%s.log" % (hid, run_num,
                                                               jobname.replace('.py', ''), logsuffix))

        if batch is None:
            arg_dict.pop('butler_repo')
            arg_dict['butler'] = butler
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


def iterate_over_slots(task, butler, data_files, **kwargs):
    """Run a task over a series of slots

    @param task (`Task`)          The pipeline task
    @param butler (`Butler`)      The data butler
    @param data_files (dict)      Dictionary with all the files need for analysis
    @param kwargs                 Passed along to the analysis function
    """

    slot_list = kwargs.get('slots', None)
    if slot_list is None:
        slot_list = sorted(data_files.keys())
    for slot in slot_list:
        slot_data = data_files[slot]
        kwargs['slot'] = slot
        task.run(butler, slot_data, **kwargs)


def iterate_over_rafts(task, butler, data_files, **kwargs):
    """Run a task over a series of rafts

    @param task (`Task`)        The pipeline task
    @param butler (`Butler`)    The data butler
    @param data_files (dict)    Dictionary with all the files need for analysis
    @param kwargs               Passed along to the analysis function
    """
    raft_list = kwargs.get('rafts', None)
    if raft_list is None:
        raft_list = sorted(data_files.keys())
    for raft in raft_list:
        raft_data = data_files[raft]
        kwargs['raft'] = raft
        iterate_over_slots(task, butler, raft_data, **kwargs)


class AnalysisBySlot(AnalysisIterator):
    """Small class to iterate an analysis task over all the slots in a raft"""
    def __init__(self, analysis_func, data_func, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param data_func (function)     Function that gets the data to analyze
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisIterator.__init__(self, EO_AnalyzeSlotTask(analysis_func), data_func, argnames)

    def call_func(self, run_num, **kwargs):
        """Call the analysis function for one run

        @param run_num (str)  The run identifier
        @param kwargs         Passed to the analysis function
        """
        butler = kwargs.pop('butler', None)
        htype, hid = self.get_hardware(butler, run_num)
        data_files = self.get_data(butler, run_num, **kwargs)

        kwargs['run_num'] = run_num
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            iterate_over_slots(self.task, butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))


class AnalysisByRaft(AnalysisIterator):
    """Small class to iterate an analysis task over all the rafts"""
    def __init__(self, analysis_func, data_func, argnames):
        """C'tor

        @param analysis_func (fuction)  The function that does that actual analysis
        @param data_func (function)     Function that gets the data to analyze
        @param argnames (list)          List of the keyword arguments need by that function.
                                        Used to look up defaults
        """
        AnalysisIterator.__init__(self, EO_AnalyzeRaftTask(analysis_func), data_func, argnames)

    def call_func(self, run_num, **kwargs):
        """Call the analysis function for one run

        @param run_num (str)  The run identifier
        @param kwargs         Passed to the analysis functions
        """
        butler = kwargs.pop('butler', None)
        htype, hid = self.get_hardware(butler, run_num)
        data_files = self.get_data(butler, run_num, **kwargs)

        kwargs['run_num'] = run_num
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            self.task.run(butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))
