## Getting Started

### Reading a VOTable File

To read a VOTable file, pass a file path to
[`parse`](../../api/astropy.io.votable.parse.html#astropy.io.votable.parse "astropy.io.votable.parse"):

```
from astropy.io.votable import parse
votable = parse("votable.xml")
```

`votable` is a [`VOTableFile`](../../api/astropy.io.votable.tree.VOTableFile.html#astropy.io.votable.tree.VOTableFile "astropy.io.votable.tree.VOTableFile") object, which
can be used to retrieve and manipulate the data and save it back out
to disk.

### Writing a VOTable File

This section describes writing table data in the VOTable format using the
[`votable`](ref_api.html#module-astropy.io.votable "astropy.io.votable") package directly. For some cases, however, the high-level
[High-level Unified File I/O](../unified.html#table-io) will often suffice and is somewhat more convenient to use. See
the [Unified I/O VOTable](../unified_table_votable.html#table-io-votable) section for details.

To save a VOTable file, call the
[`to_xml`](../../api/astropy.io.votable.tree.VOTableFile.html#astropy.io.votable.tree.VOTableFile.to_xml "astropy.io.votable.tree.VOTableFile.to_xml") method. It accepts
either a string or Unicode path, or a Python file-like object:

```
votable.to_xml('output.xml')
```

There are a number of data storage formats supported by
[`astropy.io.votable`](ref_api.html#module-astropy.io.votable "astropy.io.votable"). The `TABLEDATA` format is XML-based and
stores values as strings representing numbers. The `BINARY` format
is more compact, and stores numbers in base64-encoded binary. VOTable
version 1.3 adds the `BINARY2` format, which allows for masking of
any data type, including integers and bit fields which cannot be
masked in the older `BINARY` format. The storage format can be set
on a per-table basis using the [`format`](../../api/astropy.io.votable.tree.TableElement.html#astropy.io.votable.tree.TableElement.format "astropy.io.votable.tree.TableElement.format")
attribute, or globally using the
[`set_all_tables_format`](../../api/astropy.io.votable.tree.VOTableFile.html#astropy.io.votable.tree.VOTableFile.set_all_tables_format "astropy.io.votable.tree.VOTableFile.set_all_tables_format") method:

```
votable.get_first_table().format = 'binary'
votable.set_all_tables_format('binary')
votable.to_xml('binary.xml')
```

### Standard Compliance

[`astropy.io.votable.tree.TableElement`](../../api/astropy.io.votable.tree.TableElement.html#astropy.io.votable.tree.TableElement "astropy.io.votable.tree.TableElement") supports the [VOTable Format Definition
Version 1.1](https://www.ivoa.net/documents/REC/VOTable/VOTable-20040811.html),
[Version 1.2](https://www.ivoa.net/documents/VOTable/20091130/REC-VOTable-1.2.html),
[Version 1.3](https://www.ivoa.net/documents/VOTable/20130920/REC-VOTable-1.3-20130920.html),
[Version 1.4](https://www.ivoa.net/documents/VOTable/20191021/REC-VOTable-1.4-20191021.html),
and [Version 1.5](https://ivoa.net/documents/VOTable/20250116/REC-VOTable-1.5.html),
Some flexibility is provided to support the 1.0 draft version and
other nonstandard usage in the wild, see [Verifying VOTables](#verifying-votables) for more
details.

Note

Each warning and VOTABLE-specific exception emitted has a number and
is documented in more detail in [Warnings](api_exceptions.html#warnings) and
[Exceptions](api_exceptions.html#exceptions).

Output always conforms to the 1.1, 1.2, 1.3, 1.4, 1.5 spec, depending on the
input.

### Verifying VOTables

Many VOTable files in the wild do not conform to the VOTable specification. You
can set what should happen when a violation is encountered with the `verify`
keyword, which can take three values:



The `verify` keyword can be used with the [`parse()`](../../api/astropy.io.votable.parse.html#astropy.io.votable.parse "astropy.io.votable.parse")
or [`parse_single_table()`](../../api/astropy.io.votable.parse_single_table.html#astropy.io.votable.parse_single_table "astropy.io.votable.parse_single_table") functions:

```
from astropy.io.votable import parse
votable = parse("votable.xml", verify='warn')
```

It is possible to change the default `verify` value through the
[`astropy.io.votable.conf.verify`](../../api/astropy.io.votable.Conf.html#astropy.io.votable.Conf.verify "astropy.io.votable.Conf.verify") item in the
[Configuration System (astropy.config)](../../config/index.html#astropy-config).

Note that `'ignore'` or `'warn'` mean that `astropy` will attempt to
parse the VOTable, but if the specification has been violated then success
cannot be guaranteed.

It is good practice to report any errors to the author of the application that
generated the VOTable file to bring the file into compliance with the
specification.

### Data Serialization Formats

VOTable supports a number of different serialization formats.

* [TABLEDATA](http://www.ivoa.net/documents/VOTable/20130920/REC-VOTable-1.3-20130920.html#ToC36)
  stores the data in pure XML, where the numerical values are written
  as human-readable strings.
* [BINARY](http://www.ivoa.net/documents/VOTable/20130920/REC-VOTable-1.3-20130920.html#ToC38)
  is a binary representation of the data, stored in the XML as an
  opaque `base64`-encoded blob.
* [BINARY2](http://www.ivoa.net/documents/VOTable/20130920/REC-VOTable-1.3-20130920.html#ToC39)
  was added in VOTable 1.3, and is identical to “BINARY”, except that
  it explicitly records the position of missing values rather than
  identifying them by a special value.
* [FITS](http://www.ivoa.net/documents/VOTable/20130920/REC-VOTable-1.3-20130920.html#ToC37)
  stores the data in an external FITS file. This serialization is not
  supported by the [`astropy.io.votable`](ref_api.html#module-astropy.io.votable "astropy.io.votable") writer, since it requires
  writing multiple files.
* `PARQUET`
  stores the data in an external PARQUET file, similar to FITS serialization.
  Reading and writing is fully supported by the [`astropy.io.votable`](ref_api.html#module-astropy.io.votable "astropy.io.votable") writer and
  the [`astropy.io.votable.parse`](../../api/astropy.io.votable.parse.html#astropy.io.votable.parse "astropy.io.votable.parse") reader. The parquet file can be
  referenced with either absolute and relative paths. The parquet
  serialization can be used as part of the unified Table I/O (see next
  section), by setting the `format` argument to `'votable.parquet'`.

The serialization format can be selected in two ways:

> 1) By setting the `format` attribute of a
> [`astropy.io.votable.tree.TableElement`](../../api/astropy.io.votable.tree.TableElement.html#astropy.io.votable.tree.TableElement "astropy.io.votable.tree.TableElement") object:
>
> ```
> votable.get_first_table().format = "binary"
> votable.to_xml("new_votable.xml")
> ```
>
> 2) By overriding the format of all tables using the
> `tabledata_format` keyword argument when writing out a VOTable
> file:
>
> ```
> votable.to_xml("new_votable.xml", tabledata_format="binary")
> ```

The VOTable standard does not map conceptually to an
[`astropy.table.Table`](../../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table"). However, a single table within the `VOTable`
file may be converted to and from an [`astropy.table.Table`](../../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table"):

```
from astropy.io.votable import parse_single_table
table = parse_single_table("votable.xml").to_table()
```

As a convenience, there is also a function to create an entire VOTable
file with just a single table:

```
from astropy.io.votable import from_table, writeto
votable = from_table(table)
writeto(votable, "output.xml")
```

Note

By default, `to_table` will use the `ID` attribute from the files to
create the column names for the [`Table`](../../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") object. However,
it may be that you want to use the `name` attributes instead. For this,
set the `use_names_over_ids` keyword to [`True`](https://docs.python.org/3/library/constants.html#True "(in Python v3.13)"). Note that since field
`names` are not guaranteed to be unique in the VOTable specification,
but column names are required to be unique in `numpy` structured arrays (and
thus [`astropy.table.Table`](../../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") objects), the names may be renamed by appending
numbers to the end in some cases.

### Performance Considerations

File reads will be moderately faster if the `TABLE` element includes
an [nrows](http://www.ivoa.net/documents/REC/VOTable/VOTable-20040811.html#ToC10) attribute. If the number of rows is not specified, the
record array must be resized repeatedly during load.

## Data Origin

### Introduction

Extract basic provenance information from VOTable header. The information is described in
DataOrigin IVOA note: <https://www.ivoa.net/documents/DataOrigin/>.

DataOrigin includes both the query information (such as publisher, contact, versions, etc.)
and the Dataset origin (such as Creator, bibliographic links, URL, etc.)

This API retrieves Metadata from INFO in VOTable.

### Getting Started

To extract DataOrigin from VOTable

Example: VizieR catalogue J/AJ/167/18

```
>>> from astropy.io.votable import parse
>>> from astropy.io.votable.dataorigin import extract_data_origin
>>> votable = parse("https://vizier.cds.unistra.fr/viz-bin/conesearch/J/AJ/167/18/table4?RA=265.51&DEC=-22.71&SR=0.1")
>>> data_origin = extract_data_origin(votable)
>>> print(data_origin)
publisher: CDS
server_software: 7.4.5
service_protocol: ivo://ivoa.net/std/ConeSearch/v1.03
request_date: 2025-03-05T14:18:05
contact: cds-question@unistra.fr
publisher: CDS

ivoid: ivo://cds.vizier/j/aj/167/18
citation: doi:10.26093/cds/vizier.51670018
reference_url: https://cdsarc.cds.unistra.fr/viz-bin/cat/J/AJ/167/18
rights_uri: https://cds.unistra.fr/vizier-org/licences_vizier.html
creator: Hong K.
...
```

### Examples

Get the (Data Center) publisher and the Creator of the dataset

```
>>> print(data_origin.query.publisher)
CDS
>>> print(data_origin.origin[0].creator)
['Hong K.']
```

### Other capabilities

DataOrigin container includes VO Elements:

The following example extracts the citation from the header (in APA style).

```
>>> # get the Title retrieved in Element
>>> origin = data_origin.origin[0]
>>> vo_elt = origin.get_votable_element()
>>> title = vo_elt.description if vo_elt else ""
>>> print(f"APA: {','.join(origin.creator)} ({origin.publication_date[0]}). {title} [Dataset]. {data_origin.query.publisher}. {origin.citation[0]}")
APA: Hong K. (2024-11-06). Period variations of 32 contact binaries (Hong+, 2024) [Dataset]. CDS. doi:10.26093/cds/vizier.51670018
```

```
>>> votable = parse("votable.xml")
>>> dataorigin.add_data_origin_info(votable, "query", "Data center name")
>>> dataorigin.add_data_origin_info(votable.resources[0], "creator", "Author name")
```