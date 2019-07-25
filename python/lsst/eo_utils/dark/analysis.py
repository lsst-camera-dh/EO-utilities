"""Functions to analyse dark and superbias frames"""

from lsst.eo_utils.base.defaults import DEFAULT_STAT_TYPE

from lsst.eo_utils.base.config_utils import EOUtilOptions

from lsst.eo_utils.base.iter_utils import AnalysisBySlot

from lsst.eo_utils.base.image_utils import get_ccd_from_id

from lsst.eo_utils.base.analysis import AnalysisConfig, AnalysisTask

from lsst.eo_utils.dark.file_utils import get_dark_files_run,\
    SLOT_DARK_TABLE_FORMATTER, SLOT_DARK_PLOT_FORMATTER,\
    SUPERDARK_FORMATTER, SUPERDARK_STAT_FORMATTER

from lsst.eo_utils.dark.butler_utils import get_dark_files_butler


class DarkAnalysisConfig(AnalysisConfig):
    """Configurate for bias analyses"""
    outdir = EOUtilOptions.clone_param('outdir')
    run = EOUtilOptions.clone_param('run')
    raft = EOUtilOptions.clone_param('raft')
    slot = EOUtilOptions.clone_param('slot')
    outsuffix = EOUtilOptions.clone_param('outsuffix')
    nfiles = EOUtilOptions.clone_param('nfiles')


class DarkAnalysisTask(AnalysisTask):
    """Simple functor class to tie together standard dark data analysis
    """

    # These can overridden by the sub-class
    ConfigClass = DarkAnalysisConfig
    _DefaultName = "DarkAnalysisTask"
    iteratorClass = AnalysisBySlot

    tablename_format = SLOT_DARK_TABLE_FORMATTER
    plotname_format = SLOT_DARK_PLOT_FORMATTER
    datatype = 'dark'

    def get_superdark_file(self, suffix, **kwargs):
        """Get the name of the superdark file for a particular run, raft, ccd...

        Parameters
        ----------
        suffix : `str`
            The filename suffix
        kwargs
            Passed to the file name formatter

        Returns
        -------
        retval : `str`
            The filename
        """
        if self.get_config_param('stat', None) in [DEFAULT_STAT_TYPE, None]:
            formatter = SUPERDARK_FORMATTER
        else:
            formatter = SUPERDARK_STAT_FORMATTER

        return self.get_filename_from_format(formatter, suffix, **kwargs)

    def get_superdark_frame(self, mask_files, **kwargs):
        """Get the superdark frame for a particular run, raft, ccd...

        Parameters
        ----------
        mask_files : `list`
            The files used to build the pixel mask
        types : `str`
            Types of frames to build ['l', 'h', 'ratio']
        kwargs
            Used to override the configuration

        Returns
        -------
        ret_val : `MaskedCCD`
            Superdark frame
        """
        self.safe_update(**kwargs)
        superdark_file = self.get_superdark_file('')
        return get_ccd_from_id(None, superdark_file, mask_files)

    def get_data(self, butler, run_num, **kwargs):
        """Get a set of sflat and mask files out of a folder

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
        kwargs.pop('run_num', None)

        if butler is None:
            retval = get_dark_files_run(run_num, **kwargs)
        else:
            retval = get_dark_files_butler(butler, run_num, **kwargs)
        if not retval:
            self.log.error("Call to get_data returned no data")
        return retval

    def extract(self, butler, data, **kwargs):
        """This needs to be implemented by the sub-class

        It should analyze the input data and create a set of tables
        in a `TableDict` object

        Parameters
        ----------
        butler : `Butler`
            The data butler
        data : `dict`
            Dictionary (or other structure) contain the input data
        kwargs
            Used to override default configuration

        Returns
        -------
        dtables : `TableDict`
            The resulting data
        """
        raise NotImplementedError("AnalysisFunc.extract is not overridden.")

    def plot(self, dtables, figs, **kwargs):
        """This needs to be implemented by the sub-class

        It should use a `TableDict` object to create a set of
        plots and fill a `FigureDict` object

        Parameters
        ----------
        dtables : `TableDict`
            The data produced by this task
        figs : `FigureDict`
            The resulting figures
        kwargs
            Used to override default configuration
        """
        raise NotImplementedError("AnalysisFunc.plot is not overridden.")
