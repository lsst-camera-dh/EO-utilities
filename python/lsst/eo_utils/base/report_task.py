"""Functions to analyse summary data from bias and superbias frames"""

import abc

import os

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import SimpleAnalysisHandler,\
    AnalysisBySlot, AnalysisByRaft, AnalysisByRun, AnalysisByDataset

from .analysis import BaseAnalysisConfig, BaseAnalysisTask

from .report_utils import write_slot_report, write_raft_report,\
    write_run_report, write_summary_report

from .file_utils import SLOT_REPORT_FORMATTER,\
    RAFT_REPORT_FORMATTER, RUN_REPORT_FORMATTER, SUMMARY_REPORT_FORMATTER,\
    make_dataids_for_run

from .factory import EO_TASK_FACTORY


class ReportConfig(BaseAnalysisConfig):
    """Configuration for html report"""
    indir = EOUtilOptions.clone_param('indir')
    htmldir = EOUtilOptions.clone_param('htmldir')
    template_file = EOUtilOptions.clone_param('template_file')
    css_file = EOUtilOptions.clone_param('css_file')
    plot_report_action = EOUtilOptions.clone_param('plot_report_action')
    overwrite = EOUtilOptions.clone_param('overwrite')
    teststand = EOUtilOptions.clone_param('teststand')

class ReportTask(BaseAnalysisTask):
    """Produce a static html report
    """

    # These can overridden by the sub-class
    ConfigClass = ReportConfig
    _DefaultName = "ReportTask"
    iteratorClass = SimpleAnalysisHandler

    tablename_format = SLOT_REPORT_FORMATTER

    datatype = 'report'

    def tablefile_name(self, **kwargs):
        """Get the name of the file for the output tables for a particular
        run, raft, ccd..

        Parameters
        ----------
        kwargs
            Used to override default configuration

        Returns
        -------
        ret_val : `str`
            The name of the file
        """
        return self.get_filename_from_format(self.tablename_format, None,
                                             **kwargs)


    def __call__(self, butler, data, **kwargs):
        """Perform the data analysis

        It is up to the iteratorClass to construct the data object that is
        passed to this function.

        Parameters
        ----------
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)
        if butler is not None:
            self.log.warn("Ignoring butler")
        self.write_report(data)

    @abc.abstractmethod
    def write_report(self, data):
        """Write a report

        Parameters
        ----------
        data : `dict`
            Dictionary (or other structure) contain the input data
        """
        raise NotImplementedError()

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
        if butler is not None:
            self.log.warn("Ignoring butler")
        return make_dataids_for_run(datakey, **kwargs)

    def io_csv_line(self, taskname, stream):
        """Write a line of comma-seperated values, used to build a table of task types"""

        md_dict = dict(raft="<RAFT>", run="<RUN>", slot="<SLOT>", dataset="<DATASET>")
        table_file = self.get_filename_from_format(self.tablename_format, '',
                                                   **md_dict).replace('None/bot/', '')
        stream.write("%-25s %-60s %-60s %-60s\n" % (taskname, 'None', table_file, 'None'))


    def io_markdown_line(self, taskname, stream):
        """Write a line of markdown, used to build a table of task types"""
        md_dict = dict(raft="<RAFT>", run="<RUN>", slot="<SLOT>", dataset="<DATASET>")
        table_file = self.get_filename_from_format(self.tablename_format, '',
                                                   **md_dict).replace('None/bot/', '')
        stream.write("| %s | %s | %s | %s |\n" % (taskname, 'None', table_file, 'None'))


class ReportSlotConfig(ReportConfig):
    """Configuration for report analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')


class ReportSlotTask(ReportTask):
    """Produce a static html report for one CCD for one run
    """

    # These can overridden by the sub-class
    ConfigClass = ReportSlotConfig
    _DefaultName = "ReportSlotTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_REPORT_FORMATTER

    def write_report(self, data):
        """Write a report

        Parameters
        ----------
        data : `dict`
            Dictionary (or other structure) contain the input data
        """
        config_kw = self.extract_config_vals(dict(template_file=None,
                                                  css_file=None,
                                                  plot_report_action=None,
                                                  overwrite=None))
        full_input = os.path.join(self.config.indir, self.config.teststand)
        write_slot_report(data, full_input, self.config.htmldir, **config_kw)


class ReportRaftConfig(ReportConfig):
    """Configuration for report analyses"""
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')


class ReportRaftTask(ReportTask):
    """Produce a static html report for one raft for one run
    """

    # These can overridden by the sub-class
    ConfigClass = ReportRaftConfig
    _DefaultName = "ReportRaftTask"
    iteratorClass = AnalysisByRaft

    tablename_format = RAFT_REPORT_FORMATTER

    def write_report(self, data):
        """Write a report

        Parameters
        ----------
        data : `dict`
            Dictionary (or other structure) contain the input data
        """
        dataid = data['S00']
        dataid.pop('slot')
        config_kw = self.extract_config_vals(dict(template_file=None,
                                                  css_file=None,
                                                  plot_report_action=None,
                                                  overwrite=None))
        full_input = os.path.join(self.config.indir, self.config.teststand)
        write_raft_report(dataid, full_input, self.config.htmldir, **config_kw)


class ReportRunConfig(ReportConfig):
    """Configuration for report analyses"""
    run = EOUtilOptions.clone_param('run')


class ReportRunTask(ReportTask):
    """Produce a static html report for one run
    """

    # These can overridden by the sub-class
    ConfigClass = ReportRunConfig
    _DefaultName = "ReportRunTask"
    iteratorClass = AnalysisByRun

    tablename_format = RUN_REPORT_FORMATTER

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
        if butler is not None:
            self.log.warn("Ignoring butler")
        return datakey

    def write_report(self, data):
        """Write a report

        Parameters
        ----------
        data : `dict`
            Dictionary (or other structure) contain the input data
        """
        config_kw = self.extract_config_vals(dict(template_file=None,
                                                  css_file=None,
                                                  plot_report_action=None,
                                                  overwrite=None))
        full_input = os.path.join(self.config.indir, self.config.teststand)
        write_run_report(data, full_input, self.config.htmldir, **config_kw)


class ReportSummaryConfig(ReportConfig):
    """Configuration for report analyses"""


class ReportSummaryTask(ReportTask):
    """Produce a static html report for all the summaries of a dataset
    """

    # These can overridden by the sub-class
    ConfigClass = ReportSummaryConfig
    _DefaultName = "ReportSummaryTask"
    iteratorClass = AnalysisByDataset

    tablename_format = SUMMARY_REPORT_FORMATTER

    def write_report(self, data):
        """Write a report

        Parameters
        ----------
        data : `dict`
            Dictionary (or other structure) contain the input data
        """
        config_kw = self.extract_config_vals(dict(template_file=None,
                                                  css_file=None,
                                                  plot_report_action=None,
                                                  overwrite=None))
        full_input = os.path.join(self.config.indir, self.config.teststand)
        write_summary_report(data, full_input, self.config.htmldir, **config_kw)


EO_TASK_FACTORY.add_task_class('ReportSlot', ReportSlotTask)
EO_TASK_FACTORY.add_task_class('ReportRaft', ReportRaftTask)
EO_TASK_FACTORY.add_task_class('ReportRun', ReportRunTask)
EO_TASK_FACTORY.add_task_class('ReportSummary', ReportSummaryTask)
