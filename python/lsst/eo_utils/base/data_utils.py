"""Functions to convert objects objects to and from astropy data tables  """

import os

import numpy as np

import h5py

from astropy.io import fits
from astropy.table import Table, Column
from astropy.table import vstack as vstack_table

# Make sure we can recognize usual suffixes
HDF5_SUFFIXS = ['.hdf', '.h5', '.hd5', '.hdf5']
FITS_SUFFIXS = ['.fit', '.fits']

class TableDict:
    """Object to collect `astropy.table.Table` objects

    This class is a dictionary mapping name to `Table`
    and a few helper functions add new tables to the dictionary
    and to read and write files, either as FITS or HDF5 files.
    """
    def __init__(self, filepath=None, tablelist=None):
        """C'tor"""
        self._table_dict = {}
        if filepath is not None:
            self.load_datatables(filepath, tablelist=tablelist)

    def keys(self):
        """Return the set of keys"""
        return self._table_dict.keys()

    def items(self):
        """Return the set of keys"""
        return self._table_dict.items()

    def __getitem__(self, key):
        """Return a particular Table

        @param key (str)   Key for the table.
        @returns (`Table`) requested Table
        """
        return self._table_dict[key]

    def get_table(self, key):
        """Return a Table"

        @param key (str)   Key for the table.
        @returns (`Table`) requested Table
        """
        return self._table_dict[key]

    def make_datatable(self, key, data):
        """Make a Table

        @param key (str)        Key for this Table
        @param data (dict)      Data for this Table

        @returns (`Table`) newly created table
        """
        tab = Table(data)
        self._table_dict[key] = tab
        return tab

    def add_datatable(self, key, tab):
        """Add a Table

        @param key (str)        Key for this Table
        @param df (dict)        Table we are adding
        """
        self._table_dict[key] = tab


    def make_datatables(self, data):
        """Make a set of Table

        @param data (dict)      Data for these `Table` objects

        @returns (dict)         Dictionary of `Table` objects
        """
        o_dict = {self.make_datatable(key, val) for key, val in data.items()}
        return o_dict


    def save_datatables(self, filepath, **kwargs):
        """Save all of the `Table` objects in this object to a file

        @param filepath (str)     The file to save it to
        @param kwargs             Passed to write functions
        """
        extype = os.path.splitext(filepath)[1]
        if extype in HDF5_SUFFIXS:
            for key, val in self._table_dict.items():
                val.write(filepath, path=key, **kwargs)
        elif extype in FITS_SUFFIXS:
            hlist = [fits.PrimaryHDU()]
            for key, val in self._table_dict.items():
                hdu = fits.table_to_hdu(val)
                hdu.name = key
                hlist.append(hdu)
            hdulist = fits.HDUList(hlist)
            hdulist.writeto(filepath, overwrite=True)
        else:
            raise ValueError("Can only write pickle and hdf5 files for now, not %s" % extype)


    def load_datatables(self, filepath, **kwargs):
        """Read a set of `Table` objects from a file into this object

        @param filepath (str)     The file to read the `Table` objects
        @param kwargs             Passed to read functions
        """
        extype = os.path.splitext(filepath)[1]
        tablelist = kwargs.get('tablelist', None)
        if extype in HDF5_SUFFIXS:
            hdffile = h5py.File(filepath)
            keys = hdffile.keys()
            for key in keys:
                if tablelist is None or key in tablelist:
                    self._table_dict[key] = Table.read(filepath, key, **kwargs)
        elif extype in FITS_SUFFIXS:
            hdulist = fits.open(filepath)
            for hdu in hdulist[1:]:
                if tablelist is None or hdu.name.lower() in tablelist:
                    self._table_dict[hdu.name.lower()] = Table.read(filepath, hdu=hdu.name)
        else:
            raise ValueError("Can only write pickle and hdf5 files for now, not %s" % extype)



def vstack_tables(filedict, **kwargs):
    """Stack a bunch of tables

    @param filedict (dict)    Dictionary pointing to the files with the tables
    @param kwargs
        tablename (str)
        keep_cols (list)
        remove_cols (list)

    @returns (Table)
    """

    kwcopy = kwargs.copy()
    tablename = kwcopy.pop('tablename')
    keep_cols = kwcopy.pop('keep_cols', None)
    remove_cols = kwcopy.pop('remove_cols', None)

    tables = []

    for irun, pair in enumerate(sorted(filedict.items())):
        dtables = TableDict(pair[1], [tablename])
        table = dtables[tablename]
        if keep_cols is not None:
            table.keep_columns(keep_cols)
        if remove_cols is not None:
            table.remove_columns(remove_cols)
        table.add_column(Column(name='run', data=irun*np.ones((len(table)), int)))
        tables.append(table)

    outtable = vstack_table(tables)
    return outtable



def get_data_column(fname, tname, cname):
    """Get a column from a particular table

    @param fname (str)     File with the tables
    @param tname (str)     Table name
    @param cname (str)     Column name

    @returns (`np.array`)
    """
    dtables = TableDict(fname, [tname])
    return dtables[tname][cname]


def get_data_columns(fname, tname, clist):
    """Get a column from a particular table

    @param fname (str)     File with the tables
    @param tname (str)     Table name
    @param clist (list)    Column names

    @returns (`np.array`)
    """
    dtables = TableDict(fname, [tname])
    dtab = dtables[tname]
    return {key:dtab[key] for key in clist}


def get_data_table_names(fname):
    """Get a column from a particular table

    @param fname (str)     File with the tables
    @returns (list)
    """
    dtables = TableDict(fname)
    return dtables.keys()


def get_data_column_names(fname, tname):
    """Get a column from a particular table

    @param fname (str)     File with the tables
    @param tname (str)     Table name

    @returns (list)
    """
    dtables = TableDict(fname, [tname])
    dtab = dtables[tname]
    return dtab.columns
