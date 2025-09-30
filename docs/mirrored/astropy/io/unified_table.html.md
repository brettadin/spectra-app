# Table Data

The [`QTable`](../api/astropy.table.QTable.html#astropy.table.QTable "astropy.table.QTable") and [`Table`](../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") classes includes two
methods, [`read()`](../api/astropy.table.Table.html#astropy.table.Table.read "astropy.table.Table.read") and [`write()`](../api/astropy.table.Table.html#astropy.table.Table.write "astropy.table.Table.write"), that
make it possible to read from and write to files. A number of formats are supported (see
[Built-in table readers/writers](#built-in-table-readers-writers)) and new file formats and extensions can be registered
with the [`Table`](../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") class (see [I/O Registry](registry.html#io-registry)).

To use this interface, first import the [`Table`](../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") class,
then call the [`Table`](../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table")
[`read()`](../api/astropy.table.Table.html#astropy.table.Table.read "astropy.table.Table.read") method with the name of the file and
the file format, for instance `'ascii.daophot'`:

```
>>> from astropy.table import Table
>>> t = Table.read('photometry.dat', format='ascii.daophot')
```

It is possible to load tables directly from the Internet using URLs. For
example, download tables from Vizier catalogues in CDS format
(`'ascii.cds'`):

```
>>> from astropy.table import Table
>>> t = Table.read("ftp://cdsarc.unistra.fr/pub/cats/VII/253/snrs.dat",
...         readme="ftp://cdsarc.unistra.fr/pub/cats/VII/253/ReadMe",
...         format="ascii.cds")
```

For certain file formats the format can be automatically detected, for
example, from the filename extension:

```
>>> t = Table.read('table.tex')
```

For writing a table, the format can be explicitly specified:

```
>>> t.write('some_filename', format='latex')
```

As for the [`read()`](../api/astropy.table.Table.html#astropy.table.Table.read "astropy.table.Table.read") method, the format may
be automatically identified in some cases.

The underlying file handler will also automatically detect various
compressed data formats and uncompress them as far as
supported by the Python installation (see
[`get_readable_fileobj()`](../api/astropy.utils.data.get_readable_fileobj.html#astropy.utils.data.get_readable_fileobj "astropy.utils.data.get_readable_fileobj")).

For writing, you can also specify details about the [Table serialization
methods](#id1) via the `serialize_method` keyword argument. This allows
fine control of the way to write out certain columns, for instance
writing an ISO format Time column as a pair of JD1/JD2 floating
point values (for full resolution) or as a formatted ISO date string.

## Built-In Table Readers/Writers

The [`Table`](../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") class has built-in support for various input
and output formats including [astropy.io.ascii](unified_table_text.html#table-io-ascii),
[FITS](unified_table_fits.html#table-io-fits), [HDF5](unified_table_hdf5.html#table-io-hdf5), [Pandas](unified_table_text.html#table-io-pandas),
[Parquet](unified_table_parquet.html#table-io-parquet), and [VO Tables](unified_table_votable.html#table-io-votable).

A full list of the supported formats and corresponding classes is shown in the
table below. The `Write` column indicates those formats that support write
functionality, and the `Suffix` column indicates the filename suffix
indicating a particular format. If the value of `Suffix` is `auto`, the
format is auto-detected from the file itself. Not all formats support
auto-detection.

## Details

### Table Serialization Methods

`astropy` supports fine-grained control of the way to write out (serialize)
the columns in a Table. For instance, if you are writing an ISO format
Time column to an ECSV text table file, you may want to write this as a pair
of JD1/JD2 floating point values for full resolution (perfect “round-trip”),
or as a formatted ISO date string so that the values are easily readable by
your other applications.

The default method for serialization depends on the format (FITS, ECSV, HDF5).
For instance HDF5 is a binary format and so it would make sense to store a Time
object as JD1/JD2, while ECSV is a flat text format and commonly you
would want to see the date in the same format as the Time object. The defaults
also reflect an attempt to minimize compatibility issues between `astropy`
versions. For instance, it was possible to write Time columns to ECSV as
formatted strings in a version prior to the ability to write as JD1/JD2
pairs, so the current default for ECSV is to write as formatted strings.

The two classes which have configurable serialization methods are [`Time`](../api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time")
and [`MaskedColumn`](../api/astropy.table.MaskedColumn.html#astropy.table.MaskedColumn "astropy.table.MaskedColumn"). The defaults for each format are listed below:

#### Examples

Start by making a table with a Time column and masked column:

```
>>> import sys
>>> from astropy.time import Time
>>> from astropy.table import Table, MaskedColumn

>>> t = Table(masked=True)
>>> t['tm'] = Time(['2000-01-01', '2000-01-02'])
>>> t['mc1'] = MaskedColumn([1.0, 2.0], mask=[True, False])
>>> t['mc2'] = MaskedColumn([3.0, 4.0], mask=[False, True])
>>> t
<Table masked=True length=2>
           tm             mc1     mc2
          Time          float64 float64
----------------------- ------- -------
2000-01-01 00:00:00.000      --     3.0
2000-01-02 00:00:00.000     2.0      --
```

Now specify that you want all [`Time`](../api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time") columns written as JD1/JD2
and the `mc1` column written as a data/mask pair and write to ECSV:

```
>>> serialize_method = {Time: 'jd1_jd2', 'mc1': 'data_mask'}
>>> t.write(sys.stdout, format='ascii.ecsv', serialize_method=serialize_method)
# %ECSV 1.0
 ...
# schema: astropy-2.0
 tm.jd1    tm.jd2  mc1  mc1.mask  mc2
2451544.0    0.5   1.0   True     3.0
2451546.0   -0.5   2.0   False     ""
```

(Spaces added for clarity)

Notice that the `tm` column has been replaced by the `tm.jd1` and `tm.jd2`
columns, and likewise a new column `mc1.mask` has appeared and it explicitly
contains the mask values. When this table is read back with the `ascii.ecsv`
reader then the original columns are reconstructed.

The `serialize_method` argument can be set in two different ways:

* As a single string like `data_mask`. This value then applies to every
  column, and is a convenient strategy for a masked table with no Time columns.
* As a [`dict`](https://docs.python.org/3/library/stdtypes.html#dict "(in Python v3.13)"), where the key can be either a single column name or a class (as
  shown in the example above), and the value is the corresponding serialization
  method.

### Reading and Writing Column Objects

Individual table columns do not have their own functions for reading and writing
but it is easy to select just a single column (here “obstime”) from a table for writing:

```
>>> from astropy.time import Time
>>> tab = Table({'name': ['AB Aur', 'SU Aur'],
...              'obstime': Time(['2013-05-23T14:23:12', '2011-11-11T11:11:11'])})
>>> tab[['obstime']].write('obstime.fits')
```

Note the notation `[['obstime']]` in the last line - indexing a table with a list of strings
gives us a new table with the columns given by the strings. Since the inner list has only
one element, the resulting table has only one column.

Then, we can read back that single-column table and extract the column from it:

```
>>> col = Table.read('obstime.fits').columns[0]
>>> type(col)
<class 'astropy.table.column.Column'>
```

### Note on Filenames

Both the [`read()`](../api/astropy.table.Table.html#astropy.table.Table.read "astropy.table.Table.read") and
[`write()`](../api/astropy.table.Table.html#astropy.table.Table.write "astropy.table.Table.write") methods can accept file paths of the form
`~/data/file.csv` or `~username/data/file.csv`. These tilde-prefixed paths
are expanded in the same way as is done by many command-line utilities, to
represent the home directory of the current or specified user, respectively.

### Command-Line Utility

Note

In v7.1, the `showtable` command is now deprecated to avoid a name clash on Debian;
use `showtable-astropy` instead. The deprecated command will be removed in a future
release.

For convenience, the command-line tool `showtable-astropy` can be used to print the
content of tables for the formats supported by the unified I/O interface.

#### Example

To view the contents of a table on the command line:

```
$ showtable-astropy astropy/io/fits/tests/data/table.fits

 target V_mag
------- -----
NGC1001  11.1
NGC1002  12.3
NGC1003  15.2
```

To get full documentation on the usage and available options, do `showtable-astropy --help`.