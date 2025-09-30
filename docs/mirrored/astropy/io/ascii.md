[`astropy.io.ascii`](ref_api.html#module-astropy.io.ascii "astropy.io.ascii") provides methods for reading and writing a wide range of
text data table formats via built-in [Extension Reader Classes](extension_classes.html#extension-reader-classes). The
emphasis is on flexibility and convenience of use, although readers can
optionally use a less flexible C-based engine for reading and writing for
improved performance.

The following shows a few of the text formats that are available, while the
section on [Supported formats](#id1) contains the full list.

The strength of [`astropy.io.ascii`](ref_api.html#module-astropy.io.ascii "astropy.io.ascii") is the support for astronomy-specific
formats (often with metadata) and specialized data types such as
[SkyCoord](../../coordinates/skycoord.html#astropy-coordinates-high-level), [Time](../../time/index.html#astropy-time), and [Quantity](../../units/quantity.html#quantity).

## Getting Started

### Reading Tables

The majority of commonly encountered text tables can be read with the
[`read()`](../../api/astropy.io.ascii.read.html#astropy.io.ascii.read "astropy.io.ascii.read") function. Assume you have a file named `sources.dat` with the
following contents:

```
obsid redshift  X      Y     object
3102  0.32      4167  4085   Q1250+568-A
877   0.22      4378  3892   "Source 82"
```

This table can be read with the following:

```
>>> from astropy.io import ascii
>>> data = ascii.read("sources.dat")
>>> print(data)
obsid redshift  X    Y      object
----- -------- ---- ---- -----------
 3102     0.32 4167 4085 Q1250+568-A
  877     0.22 4378 3892   Source 82
```

The first argument to the [`read()`](../../api/astropy.io.ascii.read.html#astropy.io.ascii.read "astropy.io.ascii.read") function can be the name of a file, a string
representation of a table, or a list of table lines. The return value
(`data` in this case) is a [Table](../../table/index.html#astropy-table) object.

By default, [`read()`](../../api/astropy.io.ascii.read.html#astropy.io.ascii.read "astropy.io.ascii.read") will try to [guess the table format](read.html#guess-formats)
by trying most of the [supported formats](#id1).

Warning

Guessing the file format is often slow for large files because the reader
tries parsing the file with every allowed format until one succeeds.
For large files it is recommended to disable guessing with `guess=False`.

If guessing the format does not work, as in the case for unusually formatted
tables, you may need to give [`astropy.io.ascii`](ref_api.html#module-astropy.io.ascii "astropy.io.ascii") additional hints about
the format.

To specify specific data types for one or more columns, use the `converters`
argument (see [Converters for Specifying Dtype](read.html#io-ascii-read-converters) for details). For instance if the
`obsid` is actually a string identifier (instead of an integer) you can read
the table with the code below. This also illustrates using the preferred
[Table interface](../unified.html#table-io) for reading:

```
>>> from astropy.table import Table
>>> sources = """
... target observatory obsid
... TW_Hya Chandra     22178
... MP_Mus XMM         0406030101"""
>>> data = Table.read(sources, format='ascii', converters={'obsid': str})
>>> data
<Table length=2>
target observatory   obsid
 str6      str7      str10
------ ----------- ----------
TW_Hya     Chandra      22178
MP_Mus         XMM 0406030101
```

### Writing Tables

The [`write()`](../../api/astropy.io.ascii.write.html#astropy.io.ascii.write "astropy.io.ascii.write") function provides a way to write a data table as a formatted text
table. Most of the input table [Supported Formats](#supported-formats) for reading are also
available for writing. This provides a great deal of flexibility in the format
for writing.

The following shows how to write a formatted text table using the [`write()`](../../api/astropy.io.ascii.write.html#astropy.io.ascii.write "astropy.io.ascii.write")
function:

```
>>> import numpy as np
>>> from astropy.io import ascii
>>> from astropy.table import Table
>>> data = Table()
>>> data['x'] = np.array([1, 2, 3], dtype=np.int32)
>>> data['y'] = data['x'] ** 2
>>> ascii.write(data, 'values.dat', overwrite=True)
```

The `values.dat` file will then contain:

It is also possible and encouraged to use the write functionality from
[`astropy.io.ascii`](ref_api.html#module-astropy.io.ascii "astropy.io.ascii") through a higher level interface in the [Data
Tables](../../table/index.html#astropy-table) package (see [High-level Unified File I/O](../unified.html#table-io) for more details). For
example:

```
>>> data.write('values.dat', format='ascii', overwrite=True)
```

Attention

**ECSV is recommended**

For a reproducible text version of your table, we recommend using the
[ECSV Format](ecsv.html#ecsv-format). This stores all the table meta-data (in particular the
column types and units) to a comment section at the beginning while
maintaining compatibility with most plain CSV readers. It also allows storing
richer data like [`SkyCoord`](../../api/astropy.coordinates.SkyCoord.html#astropy.coordinates.SkyCoord "astropy.coordinates.SkyCoord") or multidimensional or
variable-length columns. ECSV is also supported in Java by [STIL](https://www.star.bristol.ac.uk/mbt/stil) and
[TOPCAT](https://www.star.bristol.ac.uk/mbt/topcat) (see [ECSV Format](ecsv.html#ecsv-format)).

To write our simple example table to ECSV we use:

```
>>> data.write('values.ecsv', overwrite=True)
```

The `.ecsv` extension is recognized and implies using ECSV (equivalent to
`format='ascii.ecsv'`). The `values.ecsv` file will then contain:

```
# %ECSV 1.0
# ---
# datatype:
# - {name: x, datatype: int32}
# - {name: y, datatype: int32}
# schema: astropy-2.0
x y
1 1
2 4
3 9
```

## Supported Formats

A full list of the supported `format` values and corresponding format types
for text tables is given below. The `Write` column indicates which formats
support write functionality, and the `Fast` column indicates which formats
are compatible with the fast Cython/C engine for reading and writing.

## Getting Help

Some formats have additional options that can be set to control the behavior of the
reader or writer. For more information on these options, you can either see the
documentation for the specific format class (e.g. [`HTML`](../../api/astropy.io.ascii.HTML.html#astropy.io.ascii.HTML "astropy.io.ascii.HTML")) or
use the `help` function of the `read` or `write` functions. For example:

```
>>> ascii.read.help()  # Common help for all formats
>>> ascii.read.help("html")  # Common help plus "html" format-specific args
>>> ascii.write.help("latex")  # Common help plus "latex" format-specific args
```

## Performance Tips

By default, when trying to read a file the reader will guess the format, which
involves trying to read it with many different readers. For better performance
when dealing with large tables, it is recommended to specify the format and any
options explicitly, and turn off guessing as well.

### Example

If you are reading a simple CSV file with a one-line header with column names,
the following:

```
read('example.csv', format='basic', delimiter=',', guess=False)  # doctest: +SKIP
```

can be at least an order of magnitude faster than:

```
read('example.csv')  # doctest: +SKIP
```