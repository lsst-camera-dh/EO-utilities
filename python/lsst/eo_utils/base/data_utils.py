"""Functions to convert objects objects to and from astropy data tables  """

import os

import h5py

from astropy.io import fits
from astropy.table import Table

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
        df = Table(data)
        self._table_dict[key] = df
        return df

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
