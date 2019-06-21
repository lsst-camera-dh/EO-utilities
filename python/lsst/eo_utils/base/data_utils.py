"""Functions to store analysis results as astropy data tables  """

import os


import sys

import numpy as np

import h5py

from astropy.io import fits
from astropy.table import Table, Column
from astropy.table import vstack as vstack_table

import lsst.afw.geom as afwGeom

from .defaults import ALL_SLOTS

# Make sure we can recognize usual suffixes
HDF5_SUFFIXS = ['.hdf', '.h5', '.hd5', '.hdf5']
FITS_SUFFIXS = ['.fit', '.fits']

class TableDict:
    """Object to collect `astropy.table.Table` objects

    This class is a dictionary mapping name to `Table`
    and a few helper functions, e.g., to add new tables to the dictionary
    and to read and write files, either as FITS or HDF5 files.
    """
    def __init__(self, filepath=None, tablelist=None, primary=None):
        """C'tor

        if filepath is not set, an empty `TableDict` will be constructed.
        if tablelist is not set, all the tables in the fill will be read.

        Parameters
        ----------
        filepath : `str`
            The name of the file to read data from
        tablelist : `list`
            The name of the tables to read
        primary : `PrimaryHDU`
            Optional primary HDU to store if the tables are stored as FITS objects
        """
        self._primary = primary
        self._table_dict = {}
        if filepath is not None:
            self.load_datatables(filepath, tablelist=tablelist)

    def keys(self):
        """Return the names of the tables"""
        return self._table_dict.keys()

    def values(self):
        """Return the tables"""
        return self._table_dict.values()

    def items(self):
        """Return the name : `Table` pairs"""
        return self._table_dict.items()

    def __getitem__(self, key):
        """Return a `Table` by name"""
        return self._table_dict[key]

    def get_table(self, key):
        """Return a `Table` by name

        This version will return None and not raise an exception if the
        table does not exist
        """
        return self._table_dict.get(key, None)

    def make_datatable(self, key, data):
        """Make a `Table` and add it to this objedts

        Parameters
        ----------
        key : `str`
            Name of the table
        data : `dict`
            Data for `Table`.   This is passed to the `Table` constructor.

        @returns (`Table`)         Newly created table
        """
        tab = Table(data)
        self._table_dict[key] = tab
        return tab

    def add_datatable(self, key, tab):
        """Add a `Table` to this object

        Parameters
        ----------
        key : `str`
            Name of the table
        tab : `Table`
            The table.
        """
        self._table_dict[key] = tab

    def make_datatables(self, data):
        """Make a set of `Table` objects

        The input data should be a dictionary of dictionaries:
        the keys will be used as the `Table` names,
        the values will be used as to construct the `Table` objects

        Parameters
        ----------
        data : `dict`
            Dictionary of dictionaries

        Returns
        -------
        o_dict : `dict`
            Dictionary of `Table` objects
        """
        o_dict = {self.make_datatable(key, val) for key, val in data.items()}
        return o_dict


    def save_datatables(self, filepath, **kwargs):
        """Save all of the `Table` objects in this object to a file

        Parameters
        ----------
        filepath : `str`
            The file to save it to
        kwargs
            Passed to write functions

        Raises
        ------
        ValueError : If the output file type is not known.
        """
        extype = os.path.splitext(filepath)[1]
        if extype in HDF5_SUFFIXS:
            for key, val in self._table_dict.items():
                val.write(filepath, path=key, **kwargs)
        elif extype in FITS_SUFFIXS:
            if self._primary is None:
                hlist = [fits.PrimaryHDU()]
            else:
                hlist = [self._primary]
            for key, val in self._table_dict.items():
                hdu = fits.table_to_hdu(val)
                hdu.name = key
                hlist.append(hdu)
            hdulist = fits.HDUList(hlist)
            hdulist.writeto(filepath, overwrite=True, **kwargs)
        else:
            raise ValueError("Can only write pickle and hdf5 files for now, not %s" % extype)


    def load_datatables(self, filepath, **kwargs):
        """Read a set of `Table` objects from a file into this object

        Parameters
        ----------
        filepath : `str`
            The file to read
        kwargs
            Passed to reade functions

        Raises
        ------
        ValueError : If the input file type is not known.
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
            raise ValueError("Can only read pickle and hdf5 files for now, not %s" % extype)


def vstack_tables(filedict, **kwargs):
    """Stack a bunch of tables 'vertically'

    This will result in a table with the same columns, but more rows.

    Parameters
    ----------
    filedict : `dict`
        Dictionary pointing to the files with the tables

    Keywords
    --------
    tablename : `str`
        Names of table to stack
    keep_cols : `list`
        Columns to retain, if None, retain all columns
    remove_cols : `list`
        Columns to remove

    Returns
    -------
    outtable : `Table`
        The stacked `Table`
    """

    kwcopy = kwargs.copy()
    tablename = kwcopy.pop('tablename')
    keep_cols = kwcopy.pop('keep_cols', None)
    remove_cols = kwcopy.pop('remove_cols', None)

    tables = []

    for irun, pair in enumerate(sorted(filedict.items())):
        try:
            dtables = TableDict(pair[1], [tablename])
        except FileNotFoundError:
            sys.stderr.write("Warning, failed to open: %s\n" % pair[1])
            continue
        table = dtables[tablename]
        if keep_cols is not None:
            table.keep_columns(keep_cols)
        if remove_cols is not None:
            table.remove_columns(remove_cols)
        table.add_column(Column(name='run', data=irun*np.ones((len(table)), int)))
        tables.append(table)

    outtable = vstack_table(tables)
    return outtable


def construct_bbox_dict(defect_table):
    """Fill a dictionary with data about the footprints from an image

    Parameters
    ----------
    defect_table : `Table`
        Astropy table with the defects
    
    Returns
    -------
    bbox_dict : `dict`
        Dictionary with Bounding boxes, keyed by slot and amp
    """
    bbox_dict = {}
    slots = defect_table['slot']
    amps = defect_table['amp']
    x_corners = defect_table['x_corner']
    y_corners = defect_table['y_corner']
    x_sizes = defect_table['x_size']
    y_sizes = defect_table['y_size']
    for islot, amp, x_corner, y_corner, x_size, y_size in\
            zip(slots, amps, x_corners, y_corners, x_sizes, y_sizes):
        slot = ALL_SLOTS[islot]
        if slot not in bbox_dict:
            bbox_dict[slot] = {}
        slot_dict = bbox_dict[slot]
        if amp not in slot_dict:
            slot_dict[amp] = []
        bbox_list = slot_dict[amp]
        corner = afwGeom.Point2I(x_corner, y_corner)
        extent = afwGeom.Extent2I(x_size, y_size)
        bbox =  afwGeom.Box2I(corner, extent)
        bbox_list.append(bbox)
    return bbox_dict
