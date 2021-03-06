"""Class to merge together masks for a single run, raft, slot"""

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
    teststand = EOUtilOptions.clone_param('teststand')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    filekey = EOUtilOptions.clone_param('filekey', default='merged-mask')


class MaskAddTask(BaseAnalysisTask):
    """Merge together masks for a single run, raft, slot
    """
    ConfigClass = MaskAddConfig
    _DefaultName = "MaskAdd"
    iteratorClass = AnalysisBySlot

    datatype = "mask"

    def __init__(self, **kwargs):
        """C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        BaseAnalysisTask.__init__(self, **kwargs)

    def get_data(self, butler, run, **kwargs):
        """Get a set of mask files out of a folder

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
        kwargs.pop('run', None)
        if butler is None:
            retval = get_mask_files_run(run, **kwargs)
        else:
            raise NotImplementedError("Can't get mask files from Butler for %s" % self.getName())

        return retval

    def __call__(self, butler, data, **kwargs):
        """Make a mask file by or-ing together a set of other mask files

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration
        """
        self.safe_update(**kwargs)

        mask_files = data['MASK']
        if butler is not None:
            self.log.warn("Ignoring butler")

        outfile = self.get_filename_from_format(MASK_FORMATTER, '.fits')
        makedir_safe(outfile)

        add_mask_files(mask_files, outfile)


    def io_csv_line(self, taskname, stream):
        """Write a line of comma-seperated values, used to build a table of task types"""

        md_dict = dict(raft="<RAFT>", run="<RUN>", slot="<SLOT>")
        table_file = self.get_filename_from_format(MASK_FORMATTER, '', **md_dict).replace('analysis/bot/', '')
        stream.write("%-25s %-60s %-60s %-60s\n" % (taskname, 'None', table_file, 'None'))


    def io_markdown_line(self, taskname, stream):
        """Write a line of markdown, used to build a table of task types"""
        md_dict = dict(raft="<RAFT>", run="<RUN>", slot="<SLOT>")
        table_file = self.get_filename_from_format(MASK_FORMATTER, '', **md_dict).replace('analysis/bot/', '')
        stream.write("| %s | %s | %s | %s |\n" % (taskname, 'None', table_file, 'None'))


EO_TASK_FACTORY.add_task_class('MaskAdd', MaskAddTask)
