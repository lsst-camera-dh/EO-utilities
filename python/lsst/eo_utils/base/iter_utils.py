"""Tools to iterate analysis task over runs, rafts and slots"""

import sys
import os

import lsst.pex.config as pexConfig

from .defaults import NINE_RAFTS, RAFT_NAMES_DICT, getSlotList

from .config_utils import EOUtilOptions, Configurable,\
    setup_parser, add_pex_arguments,\
    make_argstring, parse_args_to_dict

from .file_utils import get_hardware_type_and_id, get_raft_names_dc, read_runlist

from .butler_utils import get_butler_by_repo, get_hardware_info, get_raft_names_butler

from .batch_utils import dispatch_job


class AnalysisHandlerConfig(pexConfig.Config):
    """Configuration for EO AnalysisHandler

    These parameters control the job execution options, such as
    sending the job to the batch farm.
    """
    batch = EOUtilOptions.clone_param('batch')
    nofail = EOUtilOptions.clone_param('nofail')
    dry_run = EOUtilOptions.clone_param('dry_run')
    logfile = EOUtilOptions.clone_param('logfile')
    batch_args = EOUtilOptions.clone_param('batch_args')
    data_source = EOUtilOptions.clone_param('data_source')


class AnalysisHandler(Configurable):
    """Cass to iterate run an analysis

    Sub-classes will need to specify a run_with_args function to actually
    call the analysis task repeatedly.\
    """

    # These can be overridden by sub-classes
    ConfigClass = AnalysisHandlerConfig
    _DefaultName = "AnalysisHandler"
    exclude_pars = []
    level = 'None'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        Configurable.__init__(self, **kwargs)
        self._task = task
        self._butler = None

    def get_butler(self, **kwargs):
        """Return a data Butler

        This uses the config.data_surce and config.teststand parameters
        to pick the correct `Butler` or `None` if not using butler

        Keywords
        --------
        teststand : `str`
            The teststand we arg getting a butler for

        Returns
        -------
        butler : `Butler`
            The requested data Butler
        """
        teststand = kwargs.get('teststand', self._task.config.teststand)

        if self.config.data_source not in ['butler', 'butler_file']:
            self._butler = None
        else:
            self._butler = get_butler_by_repo(teststand)
        return self._butler


    def add_parser_arguemnts(self, parser):
        """Add the arguments for this hander and the associated task to a parser

        Parameters
        ----------
        parser : `ArgumentParser`
            The parser we are adding arguments to
        """
        handler_group = parser.add_argument_group("handler", "Arguments for job handler")
        add_pex_arguments(handler_group, self.ConfigClass)
        task_group = parser.add_argument_group("task", "Arguments for analysis task")
        add_pex_arguments(task_group, self._task.ConfigClass, self.exclude_pars)

    def run_analysis(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        Parameters
        ----------
        kwargs
            Used to override configuration defaults
        """
        self.safe_update(**kwargs)

        parser = setup_parser()
        self.add_parser_arguemnts(parser)
        args = parser.parse_args()
        arg_dict = parse_args_to_dict(args, parser, None)
        arg_dict.update(**kwargs)

        self.run_with_args(**arg_dict)


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        Parameters
        ----------
        kwargs
            Used to override configuration defaults
        """
        raise NotImplementedError("AnalysisHandler.run_with_args")



class SimpleAnalysisHandler(AnalysisHandler):
    """Class to iterate an analysis

    This class just calls the analysis a single time
    """

    level = 'Simple'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisHandler.__init__(self, task, **kwargs)

    def call_analysis_task(self, **kwargs):
        """Just call the analysis function of the `Task`

        Parameters
        ----------
        kwargs
            Passed to the `Task`

        Keywords
        --------
        butler : `Butler`
            Data `Butler` that is being used to access data
        """
        kwargs.setdefault('butler', self._butler)
        kwargs.setdefault('handler_config', self.config)
        if kwargs.get('dry_run', False):
            self._task.info("Skipping %s" % (kwargs))
            return None
        return self._task(**kwargs)

    def get_dispatch_args(self, key, **kwargs):
        """Get the arguments to use to dispatch a sub-job

        Parameters
        ----------
        key : `str`
            Unique id for this job
        kwargs
            Passed to make_argstring()

        Returns
        -------
        ret_dict : `dict`
            Dictionary of argument name : value pairs
        """
        kwcopy = kwargs.copy()
        kwcopy.pop('task', None)
        optstring = make_argstring(self._task.config, **kwcopy)
        ret_dict = dict(optstring=optstring,
                        batch_args=self.config.batch_args,
                        batch=self.config.batch,
                        dry_run=self.config.dry_run,
                        key=key)
        try:
            ret_dict['dataset'] = self.config.dataset
        except AttributeError:
            pass
        return ret_dict

    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        if config.batch is not set, this will use call_analysis_task to
        run the analysis task in the same process.

        if config.batch is set, this will use dispatch_job() to
        run the analysis task in a different process, or on the batch farm
        or processor pool.

        Parameters
        ----------
        kwargs
            Used to update both the handler and `Task` configurations
        """
        kwremain = self.safe_update(**kwargs)
        kwremain.update(kwargs)
        if self.config.batch in ['None', 'none', None]:
            self.call_analysis_task(**kwremain)
        else:
            jobname = os.path.basename(sys.argv[0])
            dispatch_kw = self.get_dispatch_args(None, **kwremain)
            dispatch_job(jobname, self.config.logfile, **dispatch_kw)


class AnalysisIteratorConfig(AnalysisHandlerConfig):
    """Configuration for EO analysis iterator

    These control the job iteration options, basically
    the list of runs to loop over.

    Either the dataset or runs parameter can be set,
    but they should not both be set.

    If dataset is set, the file <dataset>_runs.txt is read to get a list of runs.
    If runs is set, it should be a list of runs
    """
    dataset = EOUtilOptions.clone_param('dataset')
    runs = EOUtilOptions.clone_param('runs')


class AnalysisIterator(AnalysisHandler):
    """Small class to iterate an analysis, and provied an interface to the batch system

    This class will optionally parallelize execution of the job across ccds.

    """
    ConfigClass = AnalysisIteratorConfig
    _DefaultName = "AnalysisIterator"
    exclude_pars = ['run']

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisHandler.__init__(self, task, **kwargs)


    def call_analysis_task(self, run, **kwargs):
        """Needs to be implemented by sub-classes

        Parameters
        ----------
        run : `str`
            The run id to call the `Task` with
        kwargs
            Passed to the `Task`

        """
        raise NotImplementedError("AnalysisIterator.call_analysis_task")

    def get_hardware(self, butler, run):
        """return the hardware type and hardware id for a given run

        Parameters
        ----------
        bulter : `Butler`
            The data Butler or `None` (to use data catalog)
        run : `str`
            The run number we are analyzing

        Returns
        -------
        htype : `str`
            The hardware type, either 'LCA-10134' (aka full camera) or 'LCA-11021' (single raft)
        hid : `str`
            The hardware id, e.g., RMT-004
        """
        if butler is None:
            if self._task.config.teststand == 'bot':
                retval = ('LCA-10134', 'Cryostat-0001')
            else:
                retval = get_hardware_type_and_id(run)
        else:
            retval = get_hardware_info(butler, run)
        return retval

    @staticmethod
    def get_raft_list(butler, run, teststand='bot'):
        """return the list of raft id for a given run

        Parameters
        ----------
        bulter : `Butler`
            The data Butler or `None` (to use data catalog)
        run : `str`
            The run number we are analyzing
        teststand : `str`
            Default value for the teststand

        Returns
        -------
        retval : `list`
            List of raft names
        """
        if butler is None:
            retval = get_raft_names_dc(run, teststand)
        else:
            retval = get_raft_names_butler(butler, run)
        return retval


    def get_dispatch_args(self, key, **kwargs):
        """Get the arguments to use to dispatch a sub-job

        Parameters
        ----------
        run : `str`
            The ID of the run we will analyze
        kwargs
            Passed to make_argstring()

        Returns
        -------
        ret_dict : `dict`
            Dictionary of argument name : value pairs
        """
        kwcopy = kwargs.copy()
        kwcopy.pop('task', None)
        optstring = make_argstring(self.config, **kwcopy)
        ret_dict = dict(optstring=optstring,
                        batch_args=self.config.batch_args,
                        batch=self.config.batch,
                        dry_run=self.config.dry_run,
                        run=key)
        try:
            ret_dict['dataset'] = self.config.dataset
        except AttributeError:
            pass
        return ret_dict

    def dispatch_single_run(self, run, **kwargs):
        """Run the analysis over all of the requested objects.

        Parameters
        ----------
        run : `str`
            The ID of the run we will analyze
        kwargs
            Used to update `Task` configuration
        """
        taskname = self._task.getName().replace('Task', '')
        self._task.safe_update(**kwargs)

        htype, _ = self.get_hardware(self._butler, run)
        print(htype, run)

        if self.config.batch in ['None', 'none', None]:
            self.call_analysis_task(run, **kwargs)
        elif 'slot' in self.config.batch:
            if htype == "LCA-10134":
                rafts = kwargs.pop('rafts')
                slots = kwargs.pop('slots')
                dispatch_by_raft_slot(self, taskname, run, rafts, slots, **kwargs)
            elif htype == "LCA-11021":
                slots = kwargs.pop('slots')
                dispatch_by_slot(self, taskname, run, slots, **kwargs)
        elif 'raft' in self.config.batch:
            rafts = kwargs.pop('rafts')
            dispatch_by_raft(self, taskname, run, rafts, **kwargs)
        else:
            jobname = "eo_task.py %s" % self._task.getName().replace('Task', '')
            kw_remain = self.get_dispatch_args(run, **kwargs)
            dispatch_job(jobname,
                         self.config.logfile.replace('.log', '_%s_%s.log' % (taskname, run)),
                         **kw_remain)


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        Parameters
        ----------
        kwargs
            Used to update the configuration of this handler and the associated `Task`

        Keywords
        --------
        rafts : `list` or None
            Passed to dispatch_single_run to define rafts to run over
        slots : `list` or None
            Passed to dispatch_single_run to define slots to run over
        """
        kw_remain = self.safe_update(**kwargs)

        kw_remain['slots'] = kwargs.get('slots', None)
        kw_remain['rafts'] = kwargs.get('rafts', None)
        kw_remain['dry_run'] = kwargs.get('dry_run', False)

        if self.config.dataset is not None and self.config.runs is not None:
            raise ValueError("Either runs or dataset should be set, not both")
        if self.config.dataset is not None:
            runlist = read_runlist("%s_runs.txt" % self.config.dataset)
            runs = [pair[1] for pair in runlist]
        elif self.config.runs is not None:
            runs = self.config.runs
        else:
            raise ValueError("Either runs or dataset must be set")

        self.get_butler(**kw_remain)

        for run in runs:
            if self.config.nofail:
                try:
                    self.dispatch_single_run(run, **kw_remain)
                except Exception:
                    self._task.log.warn("Run %s failed, continue to next run" % run)
            else:
                self.dispatch_single_run(run, **kw_remain)


def dispatch_by_slot(handler, taskname, run, slots, **kwargs):
    """Dispatch a job for a seriers of slots

    Parameters
    ----------
    handler : `AnalysisHandler`
        Handler that manages the analysis
    run : `str`
        The run number
    taskname : `str`
        Name of the task
    slots : `list` or `None`
        Slots to run the analysis on
    """
    jobname = "eo_task.py %s" % taskname
    kwcopy = kwargs.copy()
    if slots is None:
        slots_use = getSlotList(kwcopy['raft'])
    else:
        slots_use = slots
    for slot in slots_use:
        logfile_slot = handler.config.logfile.replace('.log', '_%s_%s_%s.log' % (taskname, run, slot))
        kwcopy['slots'] = slot
        kw_remain = handler.get_dispatch_args(run, **kwcopy)
        dispatch_job(jobname, logfile_slot, **kw_remain)


def dispatch_by_raft_slot(handler, taskname, run, rafts, slots, **kwargs):
    """Dispatch a job for a seriers of slots

    Parameters
    ----------
    handler : `AnalysisHandler`
        Handler that manages the analysis
    taskname : `str`
        Name of the task
    run : `run`
        The run number
    rafts : `list` or `None`
        Rafts to run the analysis on
    slots : `list` or `None`
        Slots to run the analysis on
    """
    jobname = "eo_task.py %s" % taskname
    kwcopy = kwargs.copy()
    if rafts is None:
        rafts = RAFT_NAMES_DICT[kwcopy.get('teststand', 'bot')]
    for raft in rafts:
        kwcopy['rafts'] = raft
        if slots is None:
            slots_use = getSlotList(raft)
        else:
            slots_use = slots
        for slot in slots_use:
            logfile_slot = handler.config.logfile.replace('.log',
                                                          '_%s_%s_%s_%s.log' % (taskname, run, raft, slot))
            kwcopy['slots'] = slot
            kw_remain = handler.get_dispatch_args(run, **kwcopy)
            dispatch_job(jobname, logfile_slot, **kw_remain)

def dispatch_by_raft(handler, taskname, run, rafts, **kwargs):
    """Dispatch a job for a seriers of slots

    Parameters
    ----------
    handler : `AnalysisHandler`
        Handler that manages the analysis
    taskname : `str`
        Name of the task
    run : `str`
        The run number
    rafts : `list` or `None`
        Rafts to run the analysis on
    """
    jobname = "eo_task.py %s" % taskname
    kwcopy = kwargs.copy()
    if rafts is None:
        rafts = RAFT_NAMES_DICT[kwcopy.get('teststand', 'bot')]
    for raft in rafts:
        logfile_raft = handler.config.logfile.replace('.log', '_%s_%s_%s.log' % (taskname, run, raft))
        kwcopy['rafts'] = raft
        kw_remain = handler.get_dispatch_args(run, **kwcopy)
        dispatch_job(jobname, logfile_raft, **kw_remain)



def iterate_over_slots(analysis_task, butler, data_files, **kwargs):
    """Run a function over a series of slots

    Parameters
    ----------
    analysis_task : `AnalysisTask`
        Task that does the the analysis
    butler : `Butler`
        The data butler that fetches data to analyze
    data_files : `dict`
        Dictionary with all the files need for analysis
    kwargs
        Passed along to the analysis function

    Keywords
    --------
    slots : `list` or `None`
        Defines slots to run over
    """
    slot_list = kwargs.get('slots', None)
    if slot_list is None:
        slot_list = sorted(data_files.keys())
    for slot in slot_list:
        slot_data = data_files[slot]
        kwargs['slot'] = slot
        if kwargs.get('dry_run', False):
            analysis_task.log.info("Skipping {run}:{raft}:{slot}".format(**kwargs))
            continue
        analysis_task(butler, slot_data, **kwargs)


def iterate_over_rafts_slots(analysis_task, butler, data_files, **kwargs):
    """Run a task over a series of rafts and slots in each raft

    Parameters
    ----------
    analysis_task : `AnalysisTask`
        Task that does the the analysis
    butler : `Butler`
        The data butler that fetches data to analyze
    data_files : `dict`
        Dictionary with all the files need for analysis
    kwargs
        Passed along to the analysis function

    Keywords
    --------
    rafts : `list` or `None`
        Defines rafts to run over
    """
    raft_list = kwargs.get('rafts', None)
    if raft_list is None:
        raft_list = sorted(data_files.keys())
    for raft in raft_list:
        raft_data = data_files[raft]
        kwargs['raft'] = raft
        iterate_over_slots(analysis_task, butler, raft_data, **kwargs)


def iterate_over_rafts(analysis_task, butler, data_files, **kwargs):
    """Run a task over a series of rafts

    Parameters
    ----------
    analysis_task : `AnalysisTask`
        Task that does the the analysis
    butler : `Butler`
        The data butler that fetches data to analyze
    data_files : `dict`
        Dictionary with all the files need for analysis
    kwargs
        Passed along to the analysis function

    Keywords
    --------
    rafts : `list` or `None`
        Defines rafts to run over
    """
    raft_list = kwargs.get('rafts', None)
    if raft_list is None:
        raft_list = sorted(data_files.keys())
    for raft in raft_list:
        raft_data = data_files[raft]
        kwargs['raft'] = raft
        analysis_task(butler, raft_data, **kwargs)


class AnalysisBySlotConfig(AnalysisIteratorConfig):
    """Additional configuration for EO analysis iterator for slot-based analysis
    """
    slots = EOUtilOptions.clone_param('slots')
    rafts = EOUtilOptions.clone_param('rafts')


class AnalysisBySlot(AnalysisIterator):
    """Small class to iterate an analysis task over all the ccd slots

    Sub-classes will need to specify a get_data function to
    get the data to analyze for a particular run.

    This class will call get_data to get the available data for a particular
    run and then call self._task() for each ccd slot availble in that run
    """
    ConfigClass = AnalysisBySlotConfig
    _DefaultName = "AnalysisBySlot"

    exclude_pars = ['run', 'slot']
    level = 'Slot'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisIterator.__init__(self, task)

    def get_data(self, butler, datakey, **kwargs):
        """Function to get the data

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        return self._task.get_data(butler, datakey, **kwargs)

    def call_analysis_task(self, run, **kwargs):
        """Call the analysis function for one run

        Parameters
        ----------
        run : `str`
`           The run identifier
        kwargs
            Passed to get_data() and to the analysis function

        Raises
        ------
        ValueError : If the hardware type (raft or focal plane) is not recognized
        """
        kwdata = self._task.safe_update(**kwargs)
        kwdata.update(kwargs)
        kwdata['nfiles'] = self._task.config.toDict().get('nfiles', None)
        kwdata['data_source'] = self.config.data_source
        htype, hid = self.get_hardware(self._butler, run)
        data_files = self.get_data(self._butler, run, **kwdata)

        kwargs['run'] = run
        kwargs.setdefault('handler_config', self.config)

        if htype == "LCA-10134":
            iterate_over_rafts_slots(self._task, self._butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            iterate_over_slots(self._task, self._butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run, htype))


class AnalysisByRaftConfig(AnalysisIteratorConfig):
    """Additional configuration for EO analysis iterator for raft-based analysis
    """
    rafts = EOUtilOptions.clone_param('rafts')


class AnalysisByRaft(AnalysisIterator):
    """Small class to iterate an analysis task over all the rafts

    Sub-classes will need to specify a get_data function to
    get the data to analyze for a particular run.

    This class will call get_data to get the available data for a particular
    run and then call self._task() for each raft availble in that run
    """
    ConfigClass = AnalysisByRaftConfig
    _DefaultName = "AnalysisByRaft"
    exclude_pars = ['run', 'raft']
    level = 'Raft'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisIterator.__init__(self, task, **kwargs)

    def get_data(self, butler, datakey, **kwargs):
        """Function to get the data to analyze

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        kwcopy = kwargs.copy()
        kwcopy['logger'] = self._task.log
        return self._task.get_data(butler, datakey, **kwcopy)

    def call_analysis_task(self, run, **kwargs):
        """Call the analysis function for one run

        Parameters
        ----------
        run : `str`
`           The run identifier
        kwargs
            Passed to get_data() and to the analysis function

        Raises
        ------
        ValueError : If the hardware type (raft or focal plane) is not recognized
        """
        htype, hid = self.get_hardware(self._butler, run)
        kwdata = self._task.safe_update(**kwargs)
        kwdata.update(kwargs)
        kwdata['data_source'] = self.config.data_source
        data_files = self.get_data(self._butler, run, **kwdata)

        kwargs['run'] = run
        kwargs.setdefault('handler_config', self.config)

        if htype == "LCA-10134":
            iterate_over_rafts(self._task, self._butler, data_files, **kwargs)
        elif htype == "LCA-11021":
            kwargs['raft'] = hid
            if self._task is not None:
                self._task(self._butler, data_files[hid], **kwargs)
        else:
            raise ValueError("Do not recognize hardware type for run %s: %s" % (run, htype))


class TableAnalysisBySlot(AnalysisBySlot):
    """Small class to iterate an analysis function over slots"""

    level = 'Slot Table'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisBySlot.__init__(self, task, **kwargs)

    def get_data(self, butler, datakey, **kwargs):
        """Get the data to analyze

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        kwcopy = self._task.safe_update(**kwargs)
        kwcopy.update(kwargs)
        kwcopy['run'] = datakey
        kwcopy['filekey'] = self._task.config.infilekey

        rafts = AnalysisIterator.get_raft_list(butler, datakey, self._task.config.teststand)
        out_dict = {}

        formatter = self._task.intablename_format

        for raft in rafts:

            kwcopy['raft'] = raft
            slot_dict = {}

            slots = getSlotList(raft)
            for slot in slots:
                kwcopy['slot'] = slot
                datapath = self._task.get_filename_from_format(formatter, '.fits', **kwcopy)
                slot_dict[slot] = [datapath]

            out_dict[raft] = slot_dict

        return out_dict


class TableAnalysisByRaft(AnalysisByRaft):
    """Small class to iterate an analysis function over all the slots in a raft"""

    level = 'Raft Table'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisByRaft.__init__(self, task, **kwargs)

    def get_data(self, butler, datakey, **kwargs):
        """Get the data to analyze

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        kwcopy = self._task.safe_update(**kwargs)
        kwcopy.update(kwargs)
        kwcopy['run'] = datakey
        kwcopy['filekey'] = self._task.config.infilekey

        out_dict = {}
        if self.config.rafts is not None:
            raft_list = self.config.rafts
        else:
            raft_list = AnalysisIterator.get_raft_list(butler, datakey, self._task.config.teststand)

        formatter = self._task.intablename_format

        slot_list = kwcopy.get('slots', None)

        for raft in raft_list:
            kwcopy['raft'] = raft
            slot_dict = {}
            slot_list = getSlotList(slots)
            for slot in slot_list:
                kwcopy['slot'] = slot
                datapath = self._task.get_filename_from_format(formatter, '.fits', **kwcopy)
                slot_dict[slot] = datapath
            out_dict[raft] = slot_dict
        return out_dict


class AnalysisByRunConfig(AnalysisIteratorConfig):
    """Additional configuration for EO analysis iterator for raft-based analysis
    """


class AnalysisByRun(AnalysisIterator):
    """Small class to iterate an analysis task over all the rafts

    Sub-classes will need to specify a get_data function to
    get the data to analyze for a particular run.

    This class will call get_data to get the available data for a particular
    run and then call self._task() for each raft availble in that run
    """
    ConfigClass = AnalysisByRunConfig
    _DefaultName = "AnalysisByRun"
    exclude_pars = ['run']
    level = 'Run'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisIterator.__init__(self, task, **kwargs)

    def get_data(self, butler, datakey, **kwargs):
        """Function to get the data to analyze

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        return self._task.get_data(butler, datakey, **kwargs)

    def call_analysis_task(self, run, **kwargs):
        """Call the analysis function for one run

        Parameters
        ----------
        run : `str`
`           The run identifier
        kwargs
            Passed to get_data() and to the analysis function

        Raises
        ------
        ValueError : If the hardware type (raft or focal plane) is not recognized
        """
        data_files = self.get_data(self._butler, run, **kwargs)
        kwargs['run'] = run
        kwargs.setdefault('handler_config', self.config)

        if self._task is not None:
            self._task(self._butler, data_files, **kwargs)



class TableAnalysisByRun(AnalysisByRun):
    """Small class to iterate an analysis function over all the slots in a raft"""

    level = 'Run Table'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisByRun.__init__(self, task, **kwargs)

    def get_data(self, butler, datakey, **kwargs):
        """Get the data to analyze

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        kwcopy = self._task.safe_update(**kwargs)
        kwcopy.update(kwargs)

        kwcopy['run'] = datakey
        kwargs.setdefault('handler_config', self.config)
        kwcopy['filekey'] = kwargs.get('infilekey', '')

        out_dict = {}

        raft_list = AnalysisIterator.get_raft_list(butler, datakey, self._task.config.teststand)

        formatter = self._task.intablename_format

        slot_list = kwcopy.get('slots', None)

        raft_level = False
        for raft in raft_list:
            kwcopy['raft'] = raft
            if slot_list is None:
                slot_list_use = getSlotList(raft)
            else:
                slot_list_use = slot_list
            try:
                datapath = self._task.get_filename_from_format(formatter, '.fits', **kwcopy)
                if os.path.exists(datapath):
                    out_dict[raft] = datapath
                    raft_level = True
                    continue
                if raft_level:
                    print("Skipping missing raft %s" % raft)
                    continue
            except Exception:
                pass
            slot_dict = {}
            for slot in slot_list:
                kwcopy['slot'] = slot
                datapath = self._task.get_filename_from_format(formatter, '.fits', **kwcopy)
                slot_dict[slot] = datapath
            out_dict[raft] = slot_dict
        return out_dict



class AnalysisByDatasetConfig(AnalysisHandlerConfig):
    """Additional configuration for EO analysis iterator for raft-based analysis
    """
    dataset = EOUtilOptions.clone_param('dataset')


class AnalysisByDataset(SimpleAnalysisHandler):
    """Small class to iterate an analysis task over all the rafts

    Sub-classes will need to specify a get_data function to
    get the data to analyze for a particular run.

    This class will call get_data to get the available data for a particular
    run and then call self._task() for each raft availble in that run
    """
    ConfigClass = AnalysisByDatasetConfig
    _DefaultName = "AnalysisByDataset"
    level = 'Dataset'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        SimpleAnalysisHandler.__init__(self, task, **kwargs)

    def call_analysis_task(self, **kwargs):
        """Call the analysis function for one run

        Parameters
        ----------
        run : `str`
`           The run identifier
        kwargs
            Passed to get_data() and to the analysis function

        Raises
        ------
        ValueError : If the hardware type (raft or focal plane) is not recognized
        """
        kwargs.setdefault('handler_config', self.config)
        if kwargs.get('dry_run', False):
            self._task.info("Skipping %s" % (kwargs))
            return
        if self._task is not None:
            self._task(None, self.config.dataset, **kwargs)


class SummaryAnalysisIterator(AnalysisHandler):
    """Class to iterate an analysis

    Sub-classes will need to specify a get_data function to get the data to analyze.

    This class will call get_data to get the available data and then call self._task() with
    that data.

    Sub-classes will be give a function to call,which they will call with the data to analyze
    """
    level = 'Summary'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisHandler.__init__(self, task, **kwargs)

    def get_data(self, butler, **kwargs):
        """Function to get the data

        Parameters
        ----------
        butler : `Butler`
            The data butler
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by run
        """
        if butler is not None:
            self.log.warn("Ignoring butler in get_data")

        kwcopy = self._task.safe_update(**kwargs)
        kwcopy.update(**kwargs)
        kwcopy['filekey'] = self._task.config.infilekey

        infile = '%s_runs.txt' % self._task.config.dataset

        run_list = read_runlist(infile)

        formatter = self._task.intablename_format

        filedict = {}
        for runinfo in run_list:
            hid = runinfo[0].replace('-Dev', '')
            run = runinfo[1]
            if hid in ['Cryostat-0001']:
                rafts = get_raft_names_dc(run)
            else:
                rafts = [hid]

            for raft in rafts:
                run_key = "%s_%s" % (raft, run)
                kwcopy['run'] = run
                kwcopy['raft'] = raft
                filepath = self._task.get_filename_from_format(formatter, '.fits', **kwcopy)
                filedict[run_key] = filepath

        return filedict

    def call_analysis_task(self, **kwargs):
        """Call the analysis function for one run

        Parameters
        ----------
        kwargs
            Passed to get_data() and to the analysis function
        """
        kwargs.setdefault('handler_config', self.config)
        if kwargs.get('dry_run', False):
            self._task.info("Skipping %s" % (kwargs))
            return
        data_files = self.get_data(None, **kwargs)
        self._task(None, data_files, **kwargs)

    def get_dispatch_args(self, key, **kwargs):
        """Get the arguments to use to dispatch a sub-job

        Parameters
        ----------
        key : `str`
            Unique id for this job
        kwargs
            Passed to make_argstring()

        Returns
        -------
        ret_dict : `dict`
            Dictionary of argument name : value pairs
        """
        kwcopy = kwargs.copy()
        kwcopy.pop('task', None)
        optstring = make_argstring(self._task.config, **kwcopy)
        ret_dict = dict(optstring=optstring,
                        batch_args=self.config.batch_args,
                        batch=self.config.batch,
                        dry_run=self.config.dry_run,
                        key=key)
        return ret_dict


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        By default this takes the arguments from the command line
        and overrides those with any kwargs that have been provided.

        if config.batch is not set, this will use call_analysis_task to
        run the analysis task in the same process.

        if config.batch is set, this will use dispatch_job() to
        run the analysis task in a different process, or on the batch farm
        or processor pool.

        Parameters
        ----------
        kwargs
            Used to update the configuration of this handler and the associated `Task`
        """
        kw_remain = self.safe_update(**kwargs)

        if self.config.batch in ['None', 'none', None]:
            self.call_analysis_task(**kw_remain)
        else:
            jobname = os.path.basename(sys.argv[0])
            dispatch_kw = self.get_dispatch_args(None, **kw_remain)
            dispatch_job(jobname, self.config.logfile, **dispatch_kw)



class SummaryAnalysisBySlotIterator(AnalysisBySlot):
    """Class to iterate an analysis

    Sub-classes will need to specify a get_data function to get the data to analyze.

    This class will call get_data to get the available data and then call self._task() with
    that data.

    Sub-classes will be give a function to call,which they will call with the data to analyze
    """
    level = 'Summary'

    def __init__(self, task, **kwargs):
        """C'tor

        Parameters
        ----------
        task : `AnalysisTask`
            Task that this handler will run
        kwargs
            Used to override configuration defaults
        """
        AnalysisBySlot.__init__(self, task, **kwargs)


    def get_data(self, butler, datakey, **kwargs):
        """Get the data to analyze

        Parameters
        ----------
        butler : `Butler`
            The data butler
        datakey : `str`
            Run number or other id that defines the data to analyze
        kwargs
            Used to override default configuration

        Returns
        -------
        retval : `dict`
            Dictionary mapping input data by raft, slot and file type
        """
        kwcopy = kwargs.copy()
        kwargs.setdefault('handler_config', self.config)
        kwcopy['filekey'] = kwargs.get('infilekey', '')

        if self.config.dataset is not None:
            runlist = read_runlist("%s_runs.txt" % self.config.dataset)
            runs = [pair[1] for pair in runlist]
        else:
            raise ValueError("Dataset must be set")

        out_dict = {}

        formatter = self._task.intablename_format

        slot_list = kwcopy.get('slots', None)

        for run in runs:
            raft_list = NINE_RAFTS
            kwcopy['run'] = run
            for raft in raft_list:
                try:
                    slot_dict = out_dict[raft]
                except KeyError:
                    slot_dict = {}
                    out_dict[raft] = slot_dict

                kwcopy['raft'] = raft
                if slot_list is None:
                    slot_list_use = getSlotList(raft)
                else:
                    slot_list_use = slot_list
                for slot in slot_list_use:
                    kwcopy['slot'] = slot
                    datapath = self._task.get_filename_from_format(formatter, '.fits', **kwcopy)
                    try:
                        slot_dict[slot].append(datapath)
                    except KeyError:
                        slot_dict[slot] = [datapath]
        return out_dict


    def get_hardware(self, butler, run):
        """return the hardware type and hardware id for a given run

        Parameters
        ----------
        bulter : `Butler`
            The data Butler or `None` (to use data catalog)
        run : `str`
            The run number we are analyzing

        Returns
        -------
        htype : `str`
            The hardware type, either 'LCA-10134' (aka full camera) or 'LCA-11021' (single raft)
        hid : `str`
            The hardware id, e.g., RMT-004
        """
        if self._task.config.teststand == 'ts8':
            return ('LCA-11021', run)
        if self._task.config.teststand == 'bot':
            return ('LCA-10134', run)
        return None


    def dispatch_dataset(self, dataset, **kwargs):
        """Run the analysis over all of the requested objects.

        Parameters
        ----------
        dataset : `str`
            The ID of the run we will analyze
        kwargs
            Used to update `Task` configuration
        """
        taskname = self._task.getName().replace('Task', '')

        htype, _ = self.get_hardware(self._butler, dataset)

        kwcopy = kwargs.copy()
        if self.config.batch in ['None', 'none', None]:
            self.call_analysis_task(dataset, **kwcopy)
        elif 'slot' in self.config.batch:
            if htype == "LCA-10134":
                rafts = kwcopy.pop('rafts')
                slots = kwcopy.pop('slots')
                dispatch_by_raft_slot(self, taskname, dataset, rafts, slots, **kwcopy)
            elif htype == "LCA-11021":
                slots = kwcopy.pop('slots')
                dispatch_by_slot(self, taskname, dataset, slots, **kwcopy)
        elif 'raft' in self.config.batch:
            rafts = kwcopy.pop('rafts')
            dispatch_by_raft(self, taskname, dataset, rafts, **kwcopy)
        else:
            jobname = "eo_task.py %s" % self._task.getName().replace('Task', '')
            kw_remain = self.get_dispatch_args(dataset, **kwcopy)
            dispatch_job(jobname,
                         self.config.logfile.replace('.log', '_%s_%s.log' % (taskname, dataset)),
                         **kw_remain)


    def run_with_args(self, **kwargs):
        """Run the analysis over all of the requested objects.

        Parameters
        ----------
        kwargs
            Used to update the configuration of this handler and the associated `Task`

        Keywords
        --------
        rafts : `list` or None
            Passed to dispatch_single_run to define rafts to run over
        slots : `list` or None
            Passed to dispatch_single_run to define slots to run over
        """
        kw_remain = self.safe_update(**kwargs)
        kw_remain['slots'] = kwargs.get('slots', None)
        kw_remain['rafts'] = kwargs.get('rafts', None)
        kw_remain['dry_run'] = kwargs.get('dry_run', False)

        self.get_butler(**kw_remain)

        dataset = self.config.dataset

        if self.config.nofail:
            try:
                self.dispatch_dataset(dataset, **kw_remain)
            except Exception:
                self._task.log.warn("Dataset %s failed" % dataset)
        else:
            self.dispatch_dataset(dataset, **kw_remain)


    def get_dispatch_args(self, key, **kwargs):
        """Get the arguments to use to dispatch a sub-job

        Parameters
        ----------
        key : `str`
            The ID of the run we will analyze
        kwargs
            Passed to make_argstring()

        Returns
        -------
        ret_dict : `dict`
            Dictionary of argument name : value pairs
        """
        kwcopy = kwargs.copy()
        kwcopy.pop('task', None)
        kwcopy['dataset'] = key
        optstring = make_argstring(self.config, **kwcopy)
        ret_dict = dict(optstring=optstring,
                        batch_args=self.config.batch_args,
                        batch=self.config.batch,
                        dry_run=self.config.dry_run)
        return ret_dict
