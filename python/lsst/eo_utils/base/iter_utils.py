"""Tools to iterate analyzes functions over sensor and rafts"""

import sys
import os


from .config_utils import setup_parser, make_argstring, get_config_values
from .file_utils import get_hardware_type_and_id, get_raft_names_dc
from .butler_utils import getButler, get_hardware_info, get_raft_names_butler

from .batch_utils import dispatch_job

# These should be taken from somewhere, not hardcoded here
ALL_SLOTS = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
ALL_RAFTS = ['R10', 'R22']


class AnalysisBase:
    """Small class to iterate run an analysis, and provied an interface to the batch system

    @param argnames (list)          List of the keyword arguments need by that function.
                                    Used to look up defaults
    """
    # These are arguments that control batch job submission
    batch_argnames = ['logfile', 'batch_args', 'batch', 'dry_run']

    argnames = None

    def __init__(self):
        """C'tor """
        self.all_argnames = []
        if self.argnames is not None:
            self.all_argnames += self.argnames
        self.all_argnames += self.batch_argnames

    @staticmethod
    def get_butler(butler_repo, **kwargs):
        """Return a data Butler

        @param: bulter_repo (str)  Key specifying the data repo
        @param kwargs (dict)       Passed to the ctor

        @returns (`Butler`)        The requested data Butler
        """
        return getButler(butler_repo, **kwargs)


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
            arg_dict = get_config_values(self.all_argnames, **kwargs)
        else:
            parser = setup_parser(self.all_argnames)
            args = parser.parse_args()
            arg_dict = args.__dict__.copy()
            arg_dict.update(**kwargs)

        self.run_with_args(**arg_dict)


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        @param kwargs    Passed to the analysis
        """
        raise NotImplementedError("AnalysisBase.call_func")


class SimpleAnalysis(AnalysisBase):
    """Small class to iterate an analysis, and provied an interface to the batch system

    @param analysis_func (function) Function that does the actual analysis for one CCD
    @param data_func (function)     Function that gets the data to analyze
    @param argnames (list)          List of the keyword arguments need by that function.
                                    Used to look up defaults
    """
    data_func = None

    def __init__(self):
        """C'tor """
        AnalysisBase.__init__(self)

    def call_func(self, **kwargs):
        """Needs to be implemented by sub-classes"""
        raise NotImplementedError("SimpoleAnalysis.call_func")

    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        @param kwargs    Passed to the analysis
        """
        batch = kwargs.pop('batch')

        if batch is None:
            self.call_func(**kwargs)
        else:
            jobname = os.path.basename(sys.argv[0])
            logfile = kwargs.pop('logfile', 'temp.log')
            batch_args = kwargs.pop('batch_args')
            kwargs['optstring'] = make_argstring(kwargs)
            kwargs['bsatch_args'] = batch_args
            dispatch_job(jobname, logfile, **kwargs)




class AnalysisIterator(AnalysisBase):
    """Small class to iterate an analysis, and provied an interface to the batch system

    @param analysis_func (function) Function that does the actual analysis for one CCD
    @param data_func (function)     Function that gets the data to analyze
    @param argnames (list)          List of the keyword arguments need by that function.
                                    Used to look up defaults
    """
    data_func = None

    def __init__(self):
        """C'tor """
        AnalysisBase.__init__(self)

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
    def get_raft_list(butler, run_num):
        """return the list of raft id for a given run

        @param: bulter (`Bulter`)  The data Butler
        @param run_num(str)        The number number we are reading

        @returns (list) of raft names
        """
        if butler is None:
            retval = get_raft_names_dc(run_num)
        else:
            retval = get_raft_names_butler(butler, run_num)
        return retval


    def get_data(self, butler, run_num, **kwargs):
        """Call the function to get the data

        @param: bulter (`Butler`)    The data Butler
        @param run_num (str)         The run identifier
        @param kwargs (dict)         Passed to the data function
        """
        if self.data_func is None:
            return None
        return self.data_func(butler, run_num, **kwargs)


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        If interactive==True then it will not use the command line
        arguments.

        If batch is not None then it will send the jobs the the batch.
        """
        run_num = kwargs.pop('run')
        batch = kwargs.pop('batch')
        butler_repo = kwargs.get('butler_repo', None)

        if butler_repo is None or kwargs.get('skip', False):
            butler = None
        else:
            butler = self.get_butler(butler_repo)

        if batch is None:
            kwargs.pop('butler_repo')
            kwargs['butler'] = butler
            self.call_func(run_num, **kwargs)
        elif batch == 'slot':
            jobname = os.path.basename(sys.argv[0])
            logfile = kwargs.get('logfile', 'temp.log')
            slots = kwargs.pop('slots')
            run = kwargs.pop('run')
            if slots is None:
                slots = ALL_SLOTS
            for slot in slots:
                kwargs['slots'] = slot
                kwargs.pop('optstring', None)
                batch_args = kwargs.pop('batch_args')
                kwargs['optstring'] = make_argstring(kwargs)
                kwargs['batch_args'] = batch_args
                logfile_slot = logfile.replace('.log', '_%s.log' % slot)
                dispatch_job(jobname, logfile_slot, run=run, **kwargs)
        else:
            jobname = os.path.basename(sys.argv[0])
            logfile = kwargs.get('logfile', 'temp.log')
            batch_args = kwargs.pop('batch_args')
            kwargs['optstring'] = make_argstring(kwargs)
            kwargs['batch_args'] = batch_args
            dispatch_job(jobname, logfile, run=run, **kwargs)


def iterate_over_slots(analysis_func, butler, data_files, **kwargs):
    """Run a task over a series of slots

    @param analysis_func (function)  Function that does the the analysis
    @param butler (`Butler`)         The data butler
    @param data_files (dict)         Dictionary with all the files need for analysis
    @param kwargs                    Passed along to the analysis function
    """

    slot_list = kwargs.get('slots', None)
    if slot_list is None:
        slot_list = sorted(data_files.keys())
    for slot in slot_list:
        slot_data = data_files[slot]
        kwargs['slot'] = slot
        analysis_func(butler, slot_data, **kwargs)


def iterate_over_rafts(analysis_func, butler, data_files, **kwargs):
    """Run a task over a series of rafts

    @param analysis_func (function)  Function that does the the analysis
    @param butler (`Butler`)         The data butler
    @param data_files (dict)         Dictionary with all the files need for analysis
    @param kwargs                    Passed along to the analysis function
    """
    raft_list = kwargs.get('rafts', None)
    if raft_list is None:
        raft_list = sorted(data_files.keys())
    for raft in raft_list:
        raft_data = data_files[raft]
        kwargs['raft'] = raft
        iterate_over_slots(analysis_func, butler, raft_data, **kwargs)


class AnalysisBySlot(AnalysisIterator):
    """Small class to iterate an analysis task over all the slots in a raft"""

    def __init__(self, analysis_func):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        """
        AnalysisIterator.__init__(self)
        self.analysis_func = analysis_func

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
            iterate_over_rafts(self.analysis_func, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            iterate_over_slots(self.analysis_func, butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))


class AnalysisByRaft(AnalysisIterator):
    """Small class to iterate an analysis task over all the rafts"""

    def __init__(self, analysis_func):
        """C'tor

        @param analysis_func (function) Function that does the actual analysis for one CCD
        """
        AnalysisIterator.__init__(self)
        self.analysis_func = analysis_func

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
            iterate_over_rafts(self.analysis_func, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            if self.analysis_func is not None:
                self.analysis_func(butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run_num, htype))


class SummaryAnalysisIterator(AnalysisBase):
    """Small class to iterate an analysis, and provied an interface to the batch system

    @param data_func (function)     Function that gets the data to analyze
    @param argnames (list)          List of the keyword arguments need by that function.
                                    Used to look up defaults
    """
    data_func = None

    def __init__(self, analysis_func):
        """C'tor """
        AnalysisBase.__init__(self)
        self.analysis_func = analysis_func

    def call_func(self, dataset, **kwargs):
        """Call the analysis function for one run

        @param run_num (str)  The run identifier
        @param kwargs         Passed to the analysis functions
        """
        data_files = self.get_data(dataset, **kwargs)

        if self.analysis_func is not None:
            self.analysis_func(data_files, **kwargs)

    def get_data(self, dataset, **kwargs):
        """Call the function to get the data

        @param: dataset (str)        The dataset set are looking at
        @param kwargs (dict)         Passed to the data function
        """
        if self.data_func is None:
            return None
        return self.data_func(dataset, **kwargs)


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        If interactive==True then it will not use the command line
        arguments.

        If batch is not None then it will send the jobs the the batch.
        """
        batch = kwargs.pop('batch')
        dataset = kwargs.pop('dataset')

        if batch is None:
            self.call_func(dataset, **kwargs)
        else:
            jobname = os.path.basename(sys.argv[0])
            logfile = kwargs.get('logfile', 'temp.log')
            batch_args = kwargs.pop('batch_args')
            kwargs['optstring'] = make_argstring(kwargs)
            kwargs['batch_args'] = batch_args
            dispatch_job(jobname, logfile, dataset=dataset, **kwargs)
