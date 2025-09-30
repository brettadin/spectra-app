# Overview of Astropy File I/O

Astropy provides two main interfaces for reading and writing data:

* [High-level Unified I/O](unified.html#io-unified) interface that is designed to be consistent
  and easy to use. This allows working with different types of data such as
  [tables](../table/index.html#astropy-table), [images](../nddata/index.html#astropy-nddata), and even
  [cosmologies](../cosmology/io/index.html#cosmology-io).
* Low-level I/O sub-packages that are directly responsible for
  reading and writing data in specific formats such as [FITS](fits/index.html#astropy-io-fits)
  or [VOTable](votable/index.html#astropy-io-votable).

In general we recommend starting with the high-level interface unless you have a
specific need for the low-level interface.