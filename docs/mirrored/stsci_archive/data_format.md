# MAST Data Format Guidelines

## Introduction

This document describes recommendations for formatting data sets
using the
[**Flexible Image Transport System**](http://fits.gsfc.nasa.gov/)
(i.e. **FITS**) format for inclusion in the
Multi-mission Archive at the Space Telescope Science Institute (MAST).
It assumes the reader is already somewhat familiar with FITS format.
The terminology used is that defined in the
 [**FITS Standard**](http://fits.gsfc.nasa.gov/fits_standard.html)

## Choosing the Appropriate FITS Format

FITS has evolved significantly during the past 5 years.
(see [**FITS history**](http://fits.gsfc.nasa.gov/iaufwg/iaufwg_activity.html)). As a result,
there is usually more than one way to store the same information
within a FITS file. Each
mission must decide which FITS format is most appropriate
for their own data sets. This may be influenced by the data analysis
software currently in place at the users institutions, since not all
FITS readers support all the currently available FITS formats.
A summary of the FITS formats used by the missions
currently supported by MAST can be found in the
[**FITS File Formats**](fits_table.html) table.
The table shows that projects have used a variety of FITS formats
for archiving data,
including all the approved FITS extensions. The one FITS format not
represented is the
[**"Random Groups Structure"**](/fits/fits_standard/node50.html). Although this format is
defined in the FITS Standard document and used for radio
interferometry
data, it has become a deprecated standard and is not recommended for
MAST archival data sets.

The [**HEASARC**](http://heasarc.gsfc.nasa.gov/)
FITS Working Group (HFWG) has adopted a set of
[**FITS file Recommendations**](http://legacy.gsfc.nasa.gov/docs/heasarc/ofwg/ofwg_recomm.html) for the high-energy astrophysics
community. The HEASARC documents describe detailed recommendations
regarding: the use of specific project-defined keywords, recommended
formats for particular types of data, the naming of table columns,
and the use of particular physical units.
Although aimed primarily at the high-energy astrophysics community,
the recommendations should be useful for
other projects as well.

Similiarly, the
[**AXAF Science Center**](http://asc.harvard.edu/index.html) (ASC) has compiled the
[**ASC FITS File Designers Guide**](http://cxc.harvard.edu/contrib/arots/fits/ascfits.ps) which
details the FITS conventions adopted by the AXAF project for
its archival data sets.
(Note the AXAF guidelines comply with the
HFWG guidelines.)

FITS [keyword conventions](http://www.lmsal.com/solarsoft/ssw_standards.html) have also been adopted at the
[Solar Data Analysis Center](http://umbra.nascom.nasa.gov/)
(SDAC) at Goddard Space Flight Center for several solar missions.

Besides the
[**FITS Support Office**](http://fits.gsfc.nasa.gov/)
at Goddard Space Flight Center,
another source for FITS documents, sample FITS files, and links to
other FITS-related sites, is the
[**FITS Archive at NRAO**](http://www.cv.nrao.edu/fits/).

**Note: the links below describing features of the FITS format
point to version 2.0 of the FITS standard
which was made available in HTML format. The latest standard
is version 3.0 which clarified some issues related to version 2
but which is not available in HTML.**

### Spectral Data

In general, we suggest storing spectral
data (i.e., data sets composed of one or more vectors)
using
[**binary table extensions**](/fits/fits_standard/node67.html). It is also possible to store vectors
in a non-homogeneous primary array, (e.g., having a row of wavelengths
followed by a row of fluxes, etc.) however it is usually more difficult to
interpret the resulting data set. Some data analysis systems have however
adopted conventions for handling these files (e.g., IRAF).

A binary table containing vector fields
seems the most logical way to store this type of data
although historically some FITS readers could not read this
format. Hopefully this has changed.
With vector fields, one row in the binary table
could contain all the data for one spectrum (e.g., a vector of
wavelengths, followed by a vector of fluxes, etc.).
Additional spectra could be stored in the same manner in the following
rows (assuming the vectors are of the same length and format).
Currently, a (possibly) more readable but less flexible
format would be to store the data in scalar fields
so that each row of the table contains all the data for one wavelength.
This implies however that the table could not be used for storing
multiple (e.g., echelle) spectra.
FITS files could however contain multiple binary tables.

If multiple spectra are to be stored which have vectors of variable length,
the project must decide between the following format options:

* pad the vectors with zeroes to a fixed length and store as vector fields
  in one table,
* use scalar fields and one spectrum per table with one wavelength/flux
  value per row in the table,
* use the  **recently-approved**  (i.e., as of April, 2005)
  variable-length array facility described in the original binary table
  extension proposal and store all spectra in one table.
  (The Copernicus raw data sets are an example of this format.)

Although non-linear wavelength values must usually be stored as
individual values,
linear wavelengths can be stored as FITS keywords
(i.e., a starting wavelength and a wavelength increment),
or, if multiple spectra are to be stored within each binary table
(e.g., one table row per spectra), the
starting wavelength and wavelength increment can be stored as scalar
data fields within the table. Note the IAU now approves the use of
vacuum wavelengths
above 2000 Angstroms, so UV data no longer need to contend
with the vacuum-to-air correction which causes a non-linearity
at 2000 Angstroms.

As mentioned before, not all processing systems support
vector fields. Earlier versions of IRAF for example, do not
support this format. Although the
[**variable-length array facility**](/fits/fits_standard/node75.html)
was only recently become an approved FITS standard, the use of vector
fields in binary tables has been an approved format since 1994, so hopefully
more FITS readers will support this format in the future.
Projects must decide which format would best serve their user community.

### Image Data

Image or multi-dimensional data can be
stored as a
[**primary array**](/fits/fits_standard/node15.html). This is the most basic FITS format and should
be readable by most if not all FITS readers.
Technically the Binary table extension can also be
used to store
[**multi-dimensional arrays**](/fits/fits_standard/node76.html), however most FITS
viewers currently require primary array FITS files. Image data can also
be scaled (using the BSCALE and BZERO keywords) to allow data to be stored
as integers rather than (larger) floating point values, however unless disk
space is an issue, it is preferable to store the data unscaled.

FITS extensions can be added
for either additional image or spectral data.
We recommend
[**image extensions**](/fits/fits_standard/node63.html) for
additional image data,
[**binary tables**](/fits/fits_standard/node67.html) for storing mixtures of ASCII and
binary data, and
[**ASCII tables**](/fits/fits_standard/node57.html) for purely ASCII data. Note ASCII tables
are particularly useful for storing "catalog-type" information.

## Keywords

Besides the
[**required FITS keywords**](/fits/fits_standard/node39.html), the project-defined keywords should
be sufficient to properly describe the included data. This
information
is also useful when included as a separate project catalog (see
[MAST Guidelines for Archiving Astrophysical
Data](mast_guidelines.html)). For processed data, it is useful to store
the processing history using
[**FITS commentary keywords**](/fits/fits_standard/node40.html#SECTION00942400000000000000) (i.e., using the HISTORY,
COMMENT, or blank keywords).
It is also strongly recommended that the project-defined file name be stored
using the FITS FILENAME keyword.

Data to be archived within MAST will be checked for proper syntax
using various FITS verification programs. The reserved FITS keywords
must follow the standard FITS conventions or they will be modified to conform.
(Surprisingly, we have found several errors in the DATE and DATE-OBS
keyword values.)
Project-specific keywords will generally not be modified. It is suggested
that the keyword comment fields be used to help define these keywords.

### Keyword Inheritance

There has been some discussion lately about whether information contained
in the primary header should be relevant to data stored in the extensions.
In other words, should the extensions "inherit" the keywords contained in the
primary header. Unfortunately, the FITS community has not reached a consensus
on how this should be handled. Some feel the extensions should be
self-contained and not linked in any way to the primary header information,
while others assume the primary header information should be considered global
and apply equally to all data in the file. Adding to the problem is the fact
that numerous FITS files were created and archived before the issue was ever
raised.

One suggestion has been to include the keyword INHERIT (with a value
of either T (true) or F (false)) in the extension headers to indicate
whether the primary header keywords apply to each particular extension.
This would help avoid
the ambiguity, however the INHERIT keyword has not been officially
reserved for this purpose.
This convention however has been adopted by the HST project and
is described in the
[STScI User's Guide
to the IRAF FITS kernel](http://stsdas.stsci.edu/stsdas/fits_userguide.html).

A survey of the existing (non-HST) MAST data sets found that inheritance
was assumed in **all** FITS files containing extensions.
In other words, **all** the MAST
archived FITS files assume that project-defined keywords in the primary
header apply to all the extensions contained within the file. In general,
the convention has been to store all the observation information in the
primary header, and store only a minimal number of FITS keywords in
the extension headers. It may be the case however, that older missions
tended to use simpler file formatsi.

It is therefore difficult to give future missions a recommendation
regarding keyword inheritance.
The choices are basically:

* assume no inheritance and duplicate all neccessary keywords
  in all extensions,
* assume keywords in the primary header are global and apply to all
  extensions, or
* use the HST convention of adding the keyword INHERIT to the
  extension headers indicating whether keyword inheritance should apply.

Perhaps the FITS community will adopt a convention for keyword
inheritance in the near future which could apply to all future
FITS files.

### Units

Another recently discussed issue has been the use of standard units
for data stored in FITS format. The current FITS standard states
units "... should conform with the recommendations in the
[IAU style manual](http://www.iau.org/science/publications/proceedings_rules/units/)
".
The problem however is that most UV spectral data
archived in MAST use Angstroms for wavelengths and ergs/cm2/s/A for
absolute fluxes, both of which are listed in the
[IAU style manual](http://www.iau.org/science/publications/proceedings_rules/units/)
as "obsolete units". As with the "keyword inheritance" issue, there is not
yet a consensus among the FITS community regarding the use
of standard units and it is therefore difficult to make a
recommendation for future missions.

### Coordinate Keywords

It is recommended that data sets include the target coordinates using
Right Ascension and Declination specified in decimal degrees. There
is currently no consensus as to the keyword names to use, but
this may be at least partly dictated by the spacecraft instrumentation.
Some of the currently used keywords are shown
in the [FITS coordinates table](fits_coordinates.html).

## File Naming Conventions

The only suggestions made for data set names are the following:

1. the name should be sufficient to uniquely identify each data set,
2. file names should be case-insensitive,
3. names should be no longer than necessary.

Historically file names following the ISO 9660 standard had a maximum
of 8 characters for the name and 3 characters for the extension.
This convention meant that files could be stored on DOS or Windows 3.1
16-bit computer systems without truncating the file name. Now that 32-bit
computers are more common, this naming convention is less important and
longer file names are common. However consider that many users
may need to ftp files between systems, and have to manually type in the
file names.

hide scripts from old browsers