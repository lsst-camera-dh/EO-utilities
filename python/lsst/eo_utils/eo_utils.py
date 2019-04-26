"""High-level interface to eo_utils package  """

import os

import sys

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

        @param kwargs:    Used to override configruation
        """
        Configurable.__init__(self, **kwargs)


    def get_task(self, key):
        """Get the class associated to a particular task name

        @param key (str)        Name associated to that class
        @returns (class)        Associated class
        """
        return self._task_factory[key]


    def get_task_defaults(self, key):
        """Get the default config values associated to a particular class

        @param key (str)        Name associated to that class
        @returns (dict) of key:default_value pairs
        """
        config_class = self._task_factory[key].ConfigClass
        ret_dict = {key:config_class._fields[key].default for key in config_class._fields.keys()}
        return ret_dict

    def run_task(self, key, **kwargs):
        """Run a particular Task

        @param key (str)        Name associated to the task class
        @param kwargs           Passed to the class run function
        """
        return self._task_factory.run_task(key, **kwargs)

    def get_task_tablefile(self, key, **kwargs):
        """Get the filenames associated to the tables producted by a particular task

        @param key (str)        Name associated to the task class
        @param kwargs           Passed to the class run function

        @returns (str)          The filename
        """
        task = self.get_task(key)
        task_defs = self.get_task_defaults(key)
        task_defs.update(**kwargs)
        return task.tablename_format(**task_defs)

    def get_task_plotfile(self, key, **kwargs):
        """Get the filenames associated to the plots producted by a particular task

        @param key (str)        Name associated to the task class
        @param kwargs           Passed to the class run function

        @returns (str)          The filename
        """
        task = self.get_task(key)
        task_defs = self.get_task_defaults(key)
        task_defs.update(**kwargs)
        return task.plotname_format(**task_defs)


    def display_plots(self, key, **kwargs):
        """Display the plots associated to a particular task

        @param key (str)        Name associated to the task class
        @param kwargs           Passed to the class run function

        @returns (str)          The filename
        """
        glob_string = self.get_task_plotfile(key, **kwargs)
        glob_string += "*"
        sys.stdout.write("Displaying %s\n" % glob_string)
        os.system("display %s" % glob_string)

    def get_filename(self, filetype, **kwargs):
        """Get a file associated to a particular CCD and run

        @param filetyple (str)  Type of file in `FileFormatDict`
        @param kwargs           Passed to the XXX_FORMAT_STRING.format statement
        """
        kwcopy = kwargs.copy()
        kwcopy.setdefault('outdir', self.config.outdir)
        return self._file_formats(filetype, **kwcopy)

    def inspect_tablefile(self, filetype, **kwargs):
        """Get a file associated to a particular CCD and run

        @param filetyple (str)  Type of file in `FileFormatDict`
        @param kwargs           Passed to the XXX_FORMAT_STRING.format statement
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

        @param filetyple (str)  Type of file in `FileFormatDict`
        @param tname (str)     Table name
        @param cname (str)     Column name
        @param kwargs          Passed to the XXX_FORMAT_STRING.format statement

        @returns (`np.array`)
        """
        fname = self.get_filename(filetype, **kwargs)
        return self.get_data_column_from_file(fname, tname, cname)

    def get_data_columns(self, filetype, tname, clist, **kwargs):
        """Get a column from a particular table

        @param filetyple (str)  Type of file in `FileFormatDict`
        @param tname (str)     Table name
        @param clist (list)    Column names
        @param kwargs          Passed to the XXX_FORMAT_STRING.format statement

        @returns (dict)
        """
        fname = self.get_filename(filetype, **kwargs)
        return self.get_data_column_from_file(fname, tname, clist)

    @staticmethod
    def get_data_column_from_file(fname, tname, cname):
        """Get a column from a particular table

        @param fname (str)     File with the tables
        @param tname (str)     Table name
        @param cname (str)     Column name

        @returns (`np.array`)
        """
        dtables = TableDict(fname, [tname])
        return dtables[tname][cname]

    @staticmethod
    def get_data_columns_from_file(fname, tname, clist):
        """Get a column from a particular table

        @param fname (str)     File with the tables
        @param tname (str)     Table name
        @param clist (list)    Column names

        @returns (`np.array`)
        """
        dtables = TableDict(fname, [tname])
        dtab = dtables[tname]
        return {key:dtab[key] for key in clist}

    @staticmethod
    def get_data_table_names_from_file(fname):
        """Get a column from a particular table

        @param fname (str)     File with the tables
        @returns (list)
        """
        dtables = TableDict(fname)
        return dtables.keys()

    @staticmethod
    def get_data_column_names_from_file(fname, tname):
        """Get a column from a particular table

        @param fname (str)     File with the tables
        @param tname (str)     Table name

        @returns (list)
        """
        dtables = TableDict(fname, [tname])
        dtab = dtables[tname]
        return dtab.columns
