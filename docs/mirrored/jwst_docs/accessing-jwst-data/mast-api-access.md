Programmatic interfaces allow discovery and access to JWST data through scripted queries, instead of using the regular web-based user interfaces. This affords a greater degree of complexity and customization in searches and retrievals. This mechanism enables one to craft searches that are both more comprehensive and more targeted in an effort to discover any and all data related to a particular object or location. The primary ways of performing these queries are through a MAST API or a Virtual Observatory service.

---

# MAST API

While scripted queries can be highly customized and efficient, there are some circumstances where using the API is *essential* for searching and retrieving JWST data. These tend to be programs that produce very large numbers of data products (tens of thousands) per observation, which can time-out or overload the MAST Portal download basket. Examples include:

* Wide field slitless spectra (WFSS) configurations of NIRCam or NIRISS, which produce level-3 products for each extracted spectrum (of which there could be thousands).
* Multicolor imaging surveys which include many dither positions as well as many spatial tiles. These produce both large numbers of science exposures, as well as many guide star files because of the associated spacecraft maneuvers.
* Lengthy moving target observations, particularly if multiple instruments or configurations are used. Again, there may be many thousands of science files, along with many thousands of guide star files as the spacecraft tracks the target.

Other examples include queries with a richer set of metadata than is available with the Portal advanced search.

Auth.MAST Tokens

Note that if you wish to download data that are protected by an Exclusive Access Period, you must be both authenticated (i.e., logged in) and authorized to obtain data for the EAP program in question. The login for API queries requires a

[MAST API Token](https://auth.mast.stsci.edu/info)

to download such data products. See

[Exclusive Access Period](/accessing-jwst-data/exclusive-access-period)

for details of which data may be affected.

---

## Python **astroquery**

Words in **bold** are GUI menus/  
panels or data software packages;   
***bold italics***are buttons in GUI  
tools or package parameters.

By far the easiest method to create custom search and retrieval scripts is to use the Python package

[**astroquery.mast**](https://astroquery.readthedocs.io/en/latest/mast/mast.html)

. This package calls most of the same back-end MAST web services as the MAST Portal, but the Python interface enables a great deal more options for customization and data analysis. It also avoids the difficult syntax of web-service queries. This package can be used both for standard queries by target/coordinates, or for searches by values of instrument keywords (e.g., for time-series observations). See

[Using MAST APIs](https://outerspace.stsci.edu/display/MASTDOCS/Using+MAST+APIs)

in the

[JWST Archive Manual](https://outerspace.stsci.edu/display/MASTDOCS/JWST+Archive+Manual)

for links to tutorials and Jupyter notebooks. A few notebooks in the MAST notebook repository may be of special interest:

* [Large Downloads](https://github.com/spacetelescope/mast_notebooks/blob/main/notebooks/multi_mission/large_downloads/large_downloads.ipynb) for downloading data from programs that would overload the Portal
* [JWST SI Keyword Search](https://spacetelescope.github.io/mast_notebooks/notebooks/JWST/SI_keyword_exoplanet_search/SI_keyword_exoplanet_search.html) for searches with rich metadata that are not available using the Portal advanced search
* [JWST Duplication Checking](https://spacetelescope.github.io/mast_notebooks/notebooks/JWST/duplication_checking/duplication_checking.html), which provides methods and advice for preparing proposals that do not duplicate existing or planned programs

## Amazon Web Services (AWS)

Publicly-available data can be retrieved from the [MAST AWS cloud registry](https://registry.opendata.aws/collab/stsci/) in two ways:

Note that data still in the exclusive access period are not available from AWS.

## Mashup

Mashup Application Programming Interface (API) provides a way to access data stored in MAST through any programming language that supports calls to standard web services, including Unix shell scripts, Perl, and Python. It does this by translating customized URL requests into database queries, which allows the user to create scripts designed to assemble specific query parameters and to send those queries in batches. This includes all capabilities of the **astroquery.mast** package, but also the ability to perform cross-matching searches with various data catalogs, and table filtering based on specific columns. This comes at a cost of managing the cumbersome syntax of web service queries and some level of programming expertise.

For detailed [service descriptions](https://mast.stsci.edu/api/v0/_services.html), instructions, and [examples of this API in use](https://mast.stsci.edu/api/v0/pyex.html)[with Python](https://mast.stsci.edu/api/v0/pyex.html)**,** please refer to the [Mashup API page](https://mast.stsci.edu/api/v0/index.html). The [MAST API Tutorial](https://mast.stsci.edu/api/v0/MastApiTutorial.html) also includes a Jupyter notebook-style example of a PythonMAST data search and retrieval.

The article [Using MAST APIs](https://outerspace.stsci.edu/display/MASTDOCS/Using+MAST+APIs) includes links to tutorials and Jupyter notebooks showing how to use scripts to access JWST data in MAST.

---

# VO services

MAST implements various protocols of the [Virtual Observatory (VO)](http://www.ivoa.net/astronomers/index.html) including those for image, table, and spectral data access. As part of these protocols, MAST core services operate using the [Common Archive Observation Model (CAOM)](http://www.opencadc.org/caom2/).  As a result, MAST data can be searched and retrieved by VO-aware applications. 

The NASA Astronomical Virtual Observatories (NAVO) program aims to provide access to data stored in some of NASA’s largest archives by creating a standardized interface for submitting queries across multiple datasets. These archives include MAST along with the [High-Energy Astrophysics Science Archive Research Center (](https://heasarc.gsfc.nasa.gov)[HEASARC](https://heasarc.gsfc.nasa.gov)[)](https://heasarc.gsfc.nasa.gov), the [Infrared Science Archive (](http://irsa.ipac.caltech.edu/frontpage/)[IRSA](http://irsa.ipac.caltech.edu/frontpage/)[)](http://irsa.ipac.caltech.edu/frontpage/), and the [NASA Extragalactic Database (NED)](https://ned.ipac.caltech.edu).

Similar to the Mashup API, VO services also primarily function by translating customized URL requests into database queries. The 4 primary types of available queries follow:

SCS, SIAP, and SSAP queries all provide broad methods of [data discovery](/accessing-jwst-data) within certain search parameters, while TAP is better suited to finding specific data as it supports more complex SQL-like queries.

More information on VO access to MAST holdings can be found [here](https://archive.stsci.edu/vo/).

---

```

```