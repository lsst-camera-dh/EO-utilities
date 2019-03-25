"""Functions to iterate over sensor and rafts"""

import sys
import os


from lsst.eo_utils.config_utils import setup_parser, EOUtilConfig, make_argstring
import lsst.pipe.base as pipeBase

from .file_utils import get_hardware_type_and_id
from .butler_utils import getButler, get_hardware_info

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



class AnalysisIterator(object):
    """Small class to iterate an analysis, and provied an interface to the batch system"""
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
        self.argnames = argnames
        self.argnames += self.batch_argnames

    def call_func(self, run_num, **kwargs):
        """Needs to be implemented by sub-classes"""
        raise NotImplementedError("AnalysisIterator.call_func")

    @staticmethod
    def get_hardware(butler, run_num):
        """return the hardware type and hardware id for a given run

        @param: bulter (Bulter)  The data Butler
        @param run_num(str)   The number number we are reading

        @returns (tuple)
            htype (str) The hardware type, either
                        'LCA-10134' (aka full camera) or
                        'LCA-11021' (single raft)
            hid (str) The hardware id, e.g., RMT-004
        """
        if butler is None:
            return get_hardware_type_and_id(run_num)
        else:
            return get_hardware_info(butler, run_num)

    @staticmethod
    def get_butler(butler_repo, **kwargs):
        """Return a data Butler

        @param: bulter_epo (str)  Key specifying the data repo
        @param kwargs (dict)      Passed to the ctor
        """
        return getButler(butler_repo, **kwargs)

    def get_data(self, butler, run_num, **kwargs):
        """Call the function to get the data

        @param: bulter (Bulter)  The data Butler
        @param run_num (str)     The run identifier
        @param kwargs (dict)     Passed to the data function
        """
        return self.data_func(butler, run_num, **kwargs)


    def run(self):
        """Run the analysis, this task the arguments from the command line using the argparse interface"""
        parser = setup_parser(self.argnames)
        args = parser.parse_args()

        if args.butler_repo is None:
            butler = None
            hinfo = get_hardware_type_and_id(args.run)
        else:
            butler = self.get_butler(args.butler_repo)
            hinfo = get_hardware_info(butler, args.run)

        jobname = os.path.basename(sys.argv[0])

        hid = hinfo[1]
        logfile = os.path.join(args.logdir, "%s_%s_%s%s.log" % (hid, args.run,
                                                                jobname.replace('.py', ''), args.logsuffix))

        arg_dict = args.__dict__.copy()
        run_num = arg_dict.pop('run')
        batch = arg_dict.pop('batch')
        arg_dict.pop('logdir')
        arg_dict.pop('logsuffix')

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

    @param task (Task)        The pipeline task
    @param butler (Butler)    The data butler
    @param data_files (dict)  Dictionary with all the files need for analysis
    @param kwargs             Passed along to the analysis function
    """

    slot_list = kwargs.get('slots', None)
    if slot_list is None:
        slot_list = ALL_SLOTS

    for slot in slot_list:
        slot_data = data_files[slot]
        kwargs['slot'] = slot
        task.run(butler, slot_data, **kwargs)


def iterate_over_rafts(task, butler, data_files, **kwargs):
    """Run a task over a series of rafts

    @param task (Task)        The pipeline task
    @param butler (Butler)    The data butler
    @param data_files (dict)  Dictionary with all the files need for analysis
    @param kwargs             Passed along to the analysis function
    """
    raft_list = kwargs.get('rafts', None)
    if raft_list is None:
        raft_list = ALL_RAFTS

    for raft in raft_list:
        raft_data = data_files[raft]
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
        @param kwargs
            db (str)    The database to look for the data
            All the remaining keyword arguments are passed to the analysis function
        """
        butler = kwargs.pop('butler', None)
        htype, hid = self.get_hardware(butler, run_num)
        data_files = self.get_data(butler, run_num, **kwargs)

        kwargs['run_num'] = run_num
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            iterate_over_slots(self.task, butler, data_files, **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))


class AnalysisByRaft(AnalysisIterator):
    """Small class to iterate an analysis task over all the raft and then all the slots in a raft"""
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
        @param kwargs
            db (str)    The database to look for the data
            All the remaining keyword arguments are passed to the analysis function
        """
        butler = kwargs.pop('butler', None)
        htype, hid = self.get_hardware(butler, run_num)
        data_files = self.get_data(butler, run_num, **kwargs)

        kwargs['run_num'] = run_num
        if htype == "LCA-10134":
            iterate_over_rafts(self.task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            self.task.run(butler, data_files, **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))
