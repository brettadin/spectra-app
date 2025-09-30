# ECVS, HDF5, Parquet, PyArrow CSV, YAML ([`astropy.io.misc`](misc_ref_api.html#module-astropy.io.misc "astropy.io.misc"))

The [`astropy.io.misc`](misc_ref_api.html#module-astropy.io.misc "astropy.io.misc") module contains miscellaneous input/output routines that
do not fit elsewhere, and are often used by other `astropy` sub-packages. For
example, [`astropy.io.misc.hdf5`](misc_ref_api.html#module-astropy.io.misc.hdf5 "astropy.io.misc.hdf5") contains functions to read/write
[`Table`](../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") objects from/to HDF5 files, but these
should not be imported directly by users. Instead, users can access this
functionality via the [`Table`](../api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") class itself (see
[High-level Unified File I/O](unified.html#table-io)). Routines that are intended to be used directly by users are
listed in the [`astropy.io.misc`](misc_ref_api.html#module-astropy.io.misc "astropy.io.misc") section.