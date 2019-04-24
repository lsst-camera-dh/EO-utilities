"""Tools to iterate analyzes functions over sensor and rafts"""

import sys
import os

import lsst.pex.config as pexConfig

from .defaults import ALL_SLOTS

from .config_utils import EOUtilConfig, Configurable,\
    setup_parser, add_pex_arguments,\
    make_argstring

from .file_utils import get_hardware_type_and_id, get_raft_names_dc, read_runlist

from .butler_utils import get_butler_by_repo, get_hardware_info, get_raft_names_butler

from .batch_utils import dispatch_job


class AnalysisHandlerConfig(pexConfig.Config):
    """Configuration for EO analysis handler

    These control the job execution options, such as
    sending the job to the batch farm.
    """
    batch = EOUtilConfig.clone_param('batch')
    dry_run = EOUtilConfig.clone_param('dry_run')
    logfile = EOUtilConfig.clone_param('logfile')
    batch_args = EOUtilConfig.clone_param('batch_args')
    butler_repo = EOUtilConfig.clone_param('butler_repo')


class AnalysisHandler(Configurable):
    """Small class to iterate run an analysis, and provied an interface to the batch system

    Sub-classes will need to specify a data_func static member to get the data to analyze.

    Sub-classes will be give a function to call,
    which they will call repeatedly with slight different options
    """
    ConfigClass = AnalysisHandlerConfig
    _DefaultName = "AnalysisHandler"

    exclude_pars = []

    def __init__(self, task, **kwargs):
        """C'tor
        @param task (`AnalysisTask`)     Task that this will run
        """
        Configurable.__init__(self, **kwargs)
        self._task = task
        self._butler = None

    def get_butler(self):
        """Return a data Butler

        @param: bulter_repo (str)  Key specifying the data repo
        @param kwargs              Passed to the Butler ctor

        @returns (`Butler`)        The requested data Butler
        """
        if self.config.butler_repo is None:
            self._butler = None
        else:
            self._butler = get_butler_by_repo(self.config.butler_repo)
        return self._butler

    def run_analysis(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        @param kwargs
             If interactive==True then it will not use the command line
             arguments.

             If batch is not None then it will send the jobs the the batch.
        """
        self.safe_update(**kwargs)

        parser = setup_parser()
        handler_group = parser.add_argument_group("handler", "Arguments for job handler")
        add_pex_arguments(handler_group, self.ConfigClass)
        task_group = parser.add_argument_group("task", "Arguments for analysis task")
        add_pex_arguments(task_group, self._task.ConfigClass, self.exclude_pars)
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
        kwargs.setdefault('butler', self._butler)
        return self._task(**kwargs)

    def get_dispatch_args(self, **kwargs):
        """Get the arguments to use to dispatch a sub-job

        @param kwargs:                Passed to job
        """
        ret_dict = dict(optstring=make_argstring(**kwargs),
                        batch_args=self.config.batch_args,
                        batch=self.config.batch,
                        dataset=self.config.dataset,
                        dry_run=self.config.dry_run)
        return ret_dict


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        @param kwargs:
            batch (str)        If this is set, send the job to the batch
            logfile (str)      Name of the log file
            batch_args (str)   Command line arguments for the batch dispatch

            The remaining kwargs are passed to the job
        """
        kwremain = self.safe_update(**kwargs)
        if self.config.batch is None:
            self.call_analysis_task(**kwremain)
        else:
            jobname = os.path.basename(sys.argv[0])
            dispatch_kw = self.get_dispatch_args(**kwremain)
            dispatch_job(jobname, self.config.logfile, **dispatch_kw)


class AnalysisIteratorConfig(AnalysisHandlerConfig):
    """Configuration for EO analysis iterator

    These control the job iteration options, basically
    the list of runs to loop over.
    """
    dataset = EOUtilConfig.clone_param('dataset')
    runs = EOUtilConfig.clone_param('runs')


class AnalysisIterator(AnalysisHandler):
    """Small class to iterate an analysis, and provied an interface to the batch system

    This class will optionally parallelize execution of the job across ccds.

    """
    ConfigClass = AnalysisIteratorConfig
    _DefaultName = "AnalysisIterator"
    exclude_pars = ['run']

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


    def get_dispatch_args(self, run, **kwargs):
        """Get the arguments to use to dispatch a sub-job

        @param run (str)              The run number
        @param kwargs:                Passed to job
        """
        if self.config.butler_repo is None:
            optstring = make_argstring(**kwargs)
        else:
            optstring = make_argstring(butler_repo=self.config.butler_repo, **kwargs)
        ret_dict = dict(optstring=optstring,
                        batch_args=self.config.batch_args,
                        batch=self.config.batch,
                        dataset=self.config.dataset,
                        dry_run=self.config.dry_run,
                        run=run)
        return ret_dict


    def dispatch_single_run(self, run, **kwargs):
        """Run the analysis over all of the requested objects.

        @param run (str)              The run number
        @param kwargs:                Passed to job
        """
        if self.config.batch is None:
            self.call_analysis_task(run, **kwargs)
        elif self.config.batch == 'slot':
            jobname = os.path.basename(sys.argv[0])
            slots = kwargs.pop('slots')
            if slots is None:
                slots = ALL_SLOTS
            for slot in slots:
                logfile_slot = self.config.logfile.replace('.log', '_%s.log' % slot)
                kwargs['slots'] = slot
                kw_remain = self.get_dispatch_args(run, **kwargs)
                dispatch_job(jobname, logfile_slot, **kw_remain)
        else:
            jobname = os.path.basename(sys.argv[0])
            kw_remain = self.get_dispatch_args(run, **kwargs)
            dispatch_job(jobname, self.config.logfile, **kw_remain)


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
        kw_remain = self.safe_update(**kwargs)
        kw_remain['slots'] = kwargs.get('slots', None)
        kw_remain['rafts'] = kwargs.get('rafts', None)

        if self.config.dataset is not None and self.config.runs is not None:
            raise ValueError("Either runs or dataset should be set, not both")
        if self.config.dataset is not None:
            runlist = read_runlist("%s_runs.txt" % self.config.dataset)
            runs = [pair[1] for pair in runlist]
        elif self.config.runs is not None:
            runs = self.config.runs
        else:
            raise ValueError("Either runs or dataset must be set")

        self.get_butler()

        for run in runs:
            self.dispatch_single_run(run, **kw_remain)


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



class AnalysisBySlotConfig(AnalysisIteratorConfig):
    """Additional configuration for EO analysis iterator for slot-based analysis
    """
    slots = EOUtilConfig.clone_param('slots')


class AnalysisBySlot(AnalysisIterator):
    """Small class to iterate an analysis task over all the ccd slots

    This class will call data_func to get the available data for a particular
    run and then call self.analysis_func for each ccd slot availble in that run
    """
    ConfigClass = AnalysisBySlotConfig
    _DefaultName = "AnalysisBySlot"

    exclude_pars = ['run', 'slot']

    def __init__(self, task):
        """C'tor
        @param task (AnalysisTask)     Task that this will run
        """
        AnalysisIterator.__init__(self, task)

    def get_data(self, butler, datakey, **kwargs):
        """Function to get the data

        @param bulter (`Butler`)     The data Butler
        @param datakey (str)         The ddata identifier (run number or other string)
        @param kwargs (dict)         Passed to the data function
        """
        raise NotImplementedError("AnalysisBySlot.get_data")

    def call_analysis_task(self, run, **kwargs):
        """Call the analysis function for one run

        @param run (str)  The run identifier
        @param kwargs         Passed to the analysis function
        """
        htype, hid = self.get_hardware(self._butler, run)
        data_files = self.get_data(self._butler, run, **kwargs)

        kwargs['run'] = run
        if htype == "LCA-10134":
            iterate_over_rafts(self._task, self._butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            iterate_over_slots(self._task, self._butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run, htype))


class AnalysisByRaftConfig(AnalysisIteratorConfig):
    """Additional configuration for EO analysis iterator for raft-based analysis
    """
    slots = EOUtilConfig.clone_param('rafts')


class AnalysisByRaft(AnalysisIterator):
    """Small class to iterate an analysis task over all the rafts

    Sub-classes will need to specify a data_func static member to
    get the data to analyze.

    This class will call data_func to get the available data for a particular
    run and then call self.analysis_func for each raft availble in that run
    """
    ConfigClass = AnalysisByRaftConfig
    _DefaultName = "AnalysisByRaft"
    exclude_pars = ['run', 'raft']

    def __init__(self, task):
        """C'tor

        @param task (`AnalysisTask`)     Task that this will run
        """
        AnalysisIterator.__init__(self, task)

    def get_data(self, butler, datakey, **kwargs):
        """Function to get the data

        @param bulter (`Butler`)     The data Butler
        @param datakey (str)         The ddata identifier (run number or other string)
        @param kwargs (dict)         Passed to the data function
        """
        raise NotImplementedError("AnalysisByRaft.get_data")

    def call_analysis_task(self, run, **kwargs):
        """Call the analysis function for one run

        @param run (str)  The run identifier
        @param kwargs         Passed to the analysis functions
        """
        htype, hid = self.get_hardware(self._butler, run)
        data_files = self.get_data(self._butler, run, **kwargs)

        kwargs['run'] = run
        if htype == "LCA-10134":
            iterate_over_rafts(self._task, self._butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            if self._task is not None:
                self._task(self._butler, data_files[hid], **kwargs)
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

    def get_data(self, butler, datakey, **kwargs):
        """Function to get the data

        @param bulter (`Butler`)     The data Butler
        @param datakey (str)         The ddata identifier (run number or other string)
        @param kwargs (dict)         Passed to the data function
        """
        raise NotImplementedError("SummaryAnalysisIterator.get_data")

    def call_analysis_task(self, dataset, **kwargs):
        """Call the analysis function for one run

        @param run (str)  The run identifier
        @param kwargs         Passed to the analysis functions
        """
        data_files = self.get_data(None, dataset, **kwargs)
        self._task(None, data_files, dataset=dataset, **kwargs)

    def get_dispatch_args(self, **kwargs):
        """Get the arguments to use to dispatch a sub-job

        @param kwargs:                Passed to job
        """
        ret_dict = dict(optstring=make_argstring(**kwargs),
                        batch_args=self.config.batch_args,
                        batch=self.config.batch,
                        dataset=self.config.dataset,
                        dry_run=self.config.dry_run)
        return ret_dict


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        If interactive==True then it will not use the command line
        arguments.

        If batch is not None then it will send the jobs the the batch.
        """
        kw_remain = self.safe_update(**kwargs)

        if self.config.batch is None:
            self.call_analysis_task(self.config.dataset, **kw_remain)
        else:
            jobname = os.path.basename(sys.argv[0])
            dispatch_kw = self.get_dispatch_args(**kw_remain)
            dispatch_job(jobname, self.config.logfile, **dispatch_kw)
