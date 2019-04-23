"""Tools to iterate analyzes functions over sensor and rafts"""

import sys
import os

from .defaults import ALL_SLOTS

from .config_utils import setup_parser, add_pex_arguments, make_argstring, get_config_values
from .file_utils import get_hardware_type_and_id, get_raft_names_dc
from .butler_utils import getButler, get_hardware_info, get_raft_names_butler

from .batch_utils import dispatch_job


class AnalysisHandler:
    """Small class to iterate run an analysis, and provied an interface to the batch system

    Sub-classes will need to specify a data_func static member to get the data to analyze.

    Sub-classes will be give a function to call,
    which they will call repeatedly with slight different options
    """
    # These are arguments that control batch job submission
    batch_argnames = ['logfile', 'batch_args', 'batch', 'dry_run']

    def __init__(self, task):
        """C'tor
        @param task (`AnalysisTask`)     Task that this will run                                        
        """
        self._task = task
        self.argnames = []  
        self.argnames += self.batch_argnames

    @staticmethod
    def get_butler(butler_repo, **kwargs):
        """Return a data Butler

        @param: bulter_repo (str)  Key specifying the data repo
        @param kwargs              Passed to the Butler ctor

        @returns (`Butler`)        The requested data Butler
        """
        return getButler(butler_repo, **kwargs)

    def get_data(self, butler, datakey, **kwargs):
        """Function to get the data

        @param bulter (`Butler`)     The data Butler
        @param datakey (str)         The ddata identifier (run number or other string)
        @param kwargs (dict)         Passed to the data function
        """
        return NotImplementedError("AnalysisHandler.get_data")

    def run_analysis(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        @param kwargs
             If interactive==True then it will not use the command line
             arguments.

             If batch is not None then it will send the jobs the the batch.
        """
        interactive = kwargs.pop('interactive', False)

        if interactive:
            arg_dict = get_config_values(self.argnames, **kwargs)
        else:
            parser = setup_parser(self.argnames)
            add_pex_arguments(parser, self._task.ConfigClass)
            args = parser.parse_args()
            arg_dict = args.__dict__.copy()
            arg_dict.update(**kwargs)

        self.run_with_args(**arg_dict)


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        @param kwargs    Passed to the analysis
        """
        raise NotImplementedError("AnalysisHandler.run_with_args")



class SimpleAnalysisHandler(AnalysisHandler):
    """Small class to iterate an analysis, and provied an interface to the batch system

    This class just calls the analysis a single time
    """
    def __init__(self, task):
        """C'tor
        @param task (AnalysisTask)     Task that this will run                                        
        """
        AnalysisHandler.__init__(self, task)

    def call_analysis_task(self, **kwargs):
        """Jusgt call the analysis function"""
        return self.task(**kwargs)

    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        @param kwargs:
            batch (str)        If this is set, send the job to the batch
            logfile (str)      Name of the log file
            batch_args (str)   Command line arguments for the batch dispatch

            The remaining kwargs are passed to the job
        """
        batch = kwargs.pop('batch')

        if batch is None:
            self.call_analysis_task(**kwargs)
        else:
            jobname = os.path.basename(sys.argv[0])
            logfile = kwargs.pop('logfile', 'temp.log')
            batch_args = kwargs.pop('batch_args')
            kwargs['optstring'] = make_argstring(kwargs)
            kwargs['batch_args'] = batch_args
            dispatch_job(jobname, logfile, **kwargs)



class AnalysisIterator(AnalysisHandler):
    """Small class to iterate an analysis, and provied an interface to the batch system

    This class will optionally parallelize execution of the job across ccds.

    """
    def __init__(self, task):
        """C'tor
        @param task (AnalysisTask)     Task that this will run                                        
        """
        AnalysisHandler.__init__(self, task)

    def call_analysis_task(self, run, **kwargs):
        """Needs to be implemented by sub-classes"""
        raise NotImplementedError("AnalysisIterator.call_analysis_task")

    @staticmethod
    def get_hardware(butler, run):
        """return the hardware type and hardware id for a given run

        @param: bulter (`Bulter`)  The data Butler
        @param run(str)        The run number we are reading

        @returns (tuple)
            htype (str) The hardware type, either
                        'LCA-10134' (aka full camera) or
                        'LCA-11021' (single raft)
            hid (str) The hardware id, e.g., RMT-004
        """
        if butler is None:
            retval = get_hardware_type_and_id(run)
        else:
            retval = get_hardware_info(butler, run)
        return retval

    @staticmethod
    def get_raft_list(butler, run):
        """return the list of raft id for a given run

        @param: bulter (`Bulter`)  The data Butler
        @param run(str)        The number number we are reading

        @returns (list) of raft names
        """
        if butler is None:
            retval = get_raft_names_dc(run)
        else:
            retval = get_raft_names_butler(butler, run)
        return retval

    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        @param kwargs:
            run (str)                 The run number
            batch (str)               Option to send jobs to the batch
            logfile (str)             Name of the log file
            batch_args (str)          Command line arguments for the batch dispatch
            skip (bool)               Skip the analysis (only make the plots)
            slots (list)              List of slot for parallel analysis
            butler_repo (str)         Name of the Butler repo
        """
        run = kwargs.pop('run')
        batch = kwargs.pop('batch')
        butler_repo = kwargs.get('butler_repo', None)

        if butler_repo is None:
            butler = None
        else:
            butler = self.get_butler(butler_repo)

        if batch is None:
            kwargs.pop('butler_repo', None)
            kwargs['butler'] = butler
            self.call_analysis_task(run, **kwargs)
        elif batch == 'slot':
            jobname = os.path.basename(sys.argv[0])
            logfile = kwargs.get('logfile', 'temp.log')
            slots = kwargs.pop('slots')
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



def iterate_over_slots(analysis_task, butler, data_files, **kwargs):
    """Run a function over a series of slots

    @param analysis_task ('AnalysisTask`)  Function that does the the analysis
    @param butler (`Butler`)               The data butler
    @param data_files (dict)               Dictionary with all the files need for analysis
    @param kwargs                          Passed along to the analysis function
    """

    slot_list = kwargs.get('slots', None)
    if slot_list is None:
        slot_list = sorted(data_files.keys())
    for slot in slot_list:
        slot_data = data_files[slot]
        kwargs['slot'] = slot
        analysis_task(butler, slot_data, **kwargs)


def iterate_over_rafts(analysis_task, butler, data_files, **kwargs):
    """Run a task over a series of rafts

    @param analysis_func ('AnalysisTask`)  Function that does the the analysis
    @param butler (`Butler`)               The data butler
    @param data_files (dict)               Dictionary with all the files need for analysis
    @param kwargs                         Passed along to the analysis function
    """
    raft_list = kwargs.get('rafts', None)
    if raft_list is None:
        raft_list = sorted(data_files.keys())
    for raft in raft_list:
        raft_data = data_files[raft]
        kwargs['raft'] = raft
        iterate_over_slots(analysis_task, butler, raft_data, **kwargs)


class AnalysisBySlot(AnalysisIterator):
    """Small class to iterate an analysis task over all the ccd slots

    This class will call data_func to get the available data for a particular
    run and then call self.analysis_func for each ccd slot availble in that run
    """
    def __init__(self, task):
        """C'tor
        @param task (AnalysisTask)     Task that this will run                                        
        """
        AnalysisIterator.__init__(self, task)
        self.argnames += ['slots']

    def call_analysis_task(self, run, **kwargs):
        """Call the analysis function for one run

        @param run (str)  The run identifier
        @param kwargs         Passed to the analysis function
        """
        butler = kwargs.pop('butler', None)
        htype, hid = self.get_hardware(butler, run)
        data_files = self.get_data(butler, run, **kwargs)

        kwargs['run'] = run
        if htype == "LCA-10134":
            iterate_over_rafts(self._task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            iterate_over_slots(self._task, butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run, htype))


class AnalysisByRaft(AnalysisIterator):
    """Small class to iterate an analysis task over all the rafts

    Sub-classes will need to specify a data_func static member to
    get the data to analyze.

    This class will call data_func to get the available data for a particular
    run and then call self.analysis_func for each raft availble in that run
    """

    def __init__(self, task):
        """C'tor

        @param task (`AnalysisTask`)     Task that this will run 
        """
        AnalysisIterator.__init__(self, task)
        self.argnames += ['rafts']


    def call_analysis_task(self, run, **kwargs):
        """Call the analysis function for one run

        @param run (str)  The run identifier
        @param kwargs         Passed to the analysis functions
        """
        butler = kwargs.pop('butler', None)
        htype, hid = self.get_hardware(butler, run)
        data_files = self.get_data(butler, run, **kwargs)

        kwargs['run'] = run
        if htype == "LCA-10134":
            iterate_over_rafts(self._task, butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            if self._task is not None:
                self._task(butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run, htype))


class SummaryAnalysisIterator(AnalysisHandler):
    """Small class to iterate an analysis, and provied an interface to the batch system

    Sub-classes will need to specify a data_func static member to get the data to analyze.

    Sub-classes will be give a function to call,which they will call with the data to analyze
    """

    def __init__(self, task):
        """C'tor
        @param task (`AnalysisTask`)     Task that this will run                                        
        """
        AnalysisHandler.__init__(self, task)

    def call_analysis_task(self, dataset, **kwargs):
        """Call the analysis function for one run

        @param run (str)  The run identifier
        @param kwargs         Passed to the analysis functions
        """
        data_files = self.get_data(None, dataset, **kwargs)
        self._task(None, data_files, dataset=dataset, **kwargs)


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
            self.call_analysis_task(dataset, **kwargs)
        else:
            jobname = os.path.basename(sys.argv[0])
            logfile = kwargs.get('logfile', 'temp.log')
            batch_args = kwargs.pop('batch_args')
            kwargs['optstring'] = make_argstring(kwargs)
            kwargs['batch_args'] = batch_args
            dispatch_job(jobname, logfile, dataset=dataset, **kwargs)
