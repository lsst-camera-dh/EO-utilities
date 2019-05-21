"""High-level interface to eo_utils package  """

import os

import sys

import numpy as np

import lsst.pex.config as pexConfig

from lsst.eo_utils.base.config_utils import Configurable, EOUtilOptions

from lsst.eo_utils.base.file_utils import FILENAME_FORMATS

from lsst.eo_utils.base.data_utils import TableDict

from lsst.eo_utils.base.factory import EO_TASK_FACTORY


class EOUtilsConfig(pexConfig.Config):
    """Configuration class for high-level interface to EOUtils"""
    outdir = EOUtilOptions.clone_param('outdir')


class EOUtils(Configurable):
    """High-level interface to EOUtils package"""

    ConfigClass = EOUtilsConfig
    _DefaultName = "EOUtils"
    _file_formats = FILENAME_FORMATS
    _task_factory = EO_TASK_FACTORY

    def __init__(self, **kwargs):
        """ C'tor

        Parameters
        ----------
        kwargs
            Used to override configruation
        """
        Configurable.__init__(self, **kwargs)


    def get_task(self, key):
        """Return a particular `Task` by name"""
        return self._task_factory[key]


    def get_task_defaults(self, key):
        """Get the default config values associated to a particular class

        Parameters
        ----------
        key : `str`
            Name associated to that `Task`

        Returns
        -------
        ret_dict : `dict`
            Dictionary of key:default_value pairs
        """
        config_class = self._task_factory[key].ConfigClass
        ret_dict = {key:config_class._fields[key].default for key in config_class._fields.keys()}
        return ret_dict

    def run_task(self, key, **kwargs):
        """Run a particular Task

        Parameters
        ----------
        key : `str`
            Name associated to that `Task`
        kwargs
            Passed to the class run function
        """
        return self._task_factory.run_task(key, **kwargs)

    def get_task_tablefile(self, key, **kwargs):
        """Get the filenames associated to the tables producted by a particular task

        Parameters
        ----------
        key : `str`
            Name associated to that `Task`
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        filename: `str`
            The filename
        """
        task = self.get_task(key)
        task_defs = self.get_task_defaults(key)
        task_defs.update(**kwargs)
        return task.tablefile_name(**task_defs)

    def get_task_plotfile(self, key, **kwargs):
        """Get the filenames associated to the plots producted by a particular task

        Parameters
        ----------
        key : `str`
            Name associated to that `Task`
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        filename: `str`
            The filename
        """
        task = self.get_task(key)
        task_defs = self.get_task_defaults(key)
        task_defs.update(**kwargs)
        return task.plotfile_name(**task_defs)


    def display_plots(self, key, **kwargs):
        """Display the plots associated to a particular task

        Parameters
        ----------
        key : `str`
            Name associated to that `Task`
        kwargs
            Passed to the class file name formatting function
        """
        glob_string = self.get_task_plotfile(key, **kwargs)
        glob_string += "*"
        sys.stdout.write("Displaying %s\n" % glob_string)
        os.system("display %s" % glob_string)

    def get_filename(self, filetype, **kwargs):
        """Get a file associated to a particular CCD and run

        Parameters
        ----------
        filetyple : `str`
            Type of file in `FileFormatDict`
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        filename: `str`
            The filename
        """
        kwcopy = kwargs.copy()
        kwcopy.setdefault('outdir', self.config.outdir)
        return self._file_formats(filetype, **kwcopy)

    def inspect_tablefile(self, filetype, **kwargs):
        """Print information about the contents of a particular
        type of file with data tables

        Parameters
        ----------
        filetyple : `str`
            Type of file in `FileFormatDict`
        kwargs
            Passed to the class file name formatting function
        """
        fname = self.get_filename(filetype, **kwargs)
        tdict = TableDict(fname)
        sys.stdout.write("File %s:\n" % fname)
        for key, val in tdict.items():
            sys.stdout.write("Table %s:\n" % key)
            for col in val.columns:
                sys.stdout.write(" %s:\n" % col)

    def get_data_column(self, filetype, tname, cname, **kwargs):
        """Get a column from a particular table

        Parameters
        ----------
        filetyple : `str`
            Type of file in `FileFormatDict`
        tname : `str`
            Table name
        cname : `str`
            Column name
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        data : `np.array`
            The requested column data
        """
        fname = self.get_filename(filetype, **kwargs)
        return self.get_data_column_from_file(fname, tname, cname)

    def get_data_columns(self, filetype, tname, clist, **kwargs):
        """Get a column from a particular table

        Parameters
        ----------
        filetyple : `str`
            Type of file in `FileFormatDict`
        tname : `str`
            Table name
        clist : `list`
            Column names
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        odict : `dict`
            Dictionary mapping column name to data
        """
        fname = self.get_filename(filetype, **kwargs)
        return self.get_data_column_from_file(fname, tname, clist)

    def get_task_table_dict(self, key, **kwargs):
        """Get the tables produceded by a particular task

        Parameters
        ----------
        key : `str`
            Name associated to that `Task`
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        tdict: `TableDict`
            The tables produced by the task/ configuration
        """
        tfile = self.get_task_tablefile(key, **kwargs) + '.fits'
        tdict = TableDict(tfile)
        return tdict


    def get_summary_data_run(self, task, tablename, run, cols, **kwargs):
        """Get the rows that match a particular run

        Parameters
        ----------
        task : `str`
            The name of the task in question
        tablename : `str`
            The name of the table in question
        run : `str`
            The run in question
        cols : `list`
            The columns to fetch

        Returns
        -------
        data : `dict`
            Dictonary mapping name : array
        """
        tdict = self.get_task_table_dict('EOResultsSummary', **kwargs)
        datatable = tdict[tablename]
        mask = self.get_run_mask(datatable, tdict['runs'], run)
        data = { col: datatable[col][mask] for col in cols }
        return data

    @staticmethod
    def get_run_mask(data_table, run_table, run):
        """Get the rows that match a particular run

        Parameters
        ----------
        data_table : `Table`
            The table with the data
        run_table : `Table`
            The table with the run ids
        run : `str`
            The run in question

        Returns
        -------
        mask : `np.array`
            The masking array
        """
        mask = data_table['run'] == np.argmax(run_table['runs'] == run)
        return mask

    @staticmethod
    def get_data_column_from_file(fname, tname, cname):
        """Get a column from a particular table

        Parameters
        ----------
        fname : `str`
            File name
        tname : `str`
            Table name
        cname : `str`
            Column name
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        data : `np.array`
            The requested column data
       """
        dtables = TableDict(fname, [tname])
        return dtables[tname][cname]

    @staticmethod
    def get_data_columns_from_file(fname, tname, clist):
        """Get a column from a particular table

        Parameters
        ----------
        filetyple : `str`
            Type of file in `FileFormatDict`
        tname : `str`
            Table name
        clist : `list`
            Column names
        kwargs
            Passed to the class file name formatting function

        Returns
        -------
        odict : `dict`
            Dictionary mapping column name to data
        """
        dtables = TableDict(fname, [tname])
        dtab = dtables[tname]
        return {key:dtab[key] for key in clist}

    @staticmethod
    def get_data_table_names_from_file(fname):
        """Get a name of tables in a particular file

        Parameters
        ----------
        fname : `str`
            File name

        Returns
        -------
        keys : `list`
            Table names
        """
        dtables = TableDict(fname)
        return dtables.keys()

    @staticmethod
    def get_data_column_names_from_file(fname, tname):
        """Get a column names from a particular table

        Parameters
        ----------
        fname : `str`
            File name
        tname : `str`
            Table name

        Returns
        -------
        keys : `list`
            Table names
        """
        dtables = TableDict(fname, [tname])
        dtab = dtables[tname]
        return dtab.columns
