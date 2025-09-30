This module can be used to query the Ned web service. All queries other than
image and spectra queries return results in a [`Table`](https://docs.astropy.org/en/stable/api/astropy.table.Table.html#astropy.table.Table "(in Astropy v7.1)"). Image
and spectra queries on the other hand return the results as a list of
[`HDUList`](https://docs.astropy.org/en/stable/io/fits/api/hdulists.html#astropy.io.fits.HDUList "(in Astropy v7.1)") objects. Below are some working examples that
illustrate common use cases.

### Query a region

These queries may be used for querying a region around a named object or
coordinates (i.e *near name* and *near position* queries). The radius of
the region should be specified in degrees or equivalent units. An easy way to do this is to use an
[`Quantity`](https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity "(in Astropy v7.1)") object to specify the radius and units. The radius may also
be specified as a string in which case it will be parsed using
[`Angle`](https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html#astropy.coordinates.Angle "(in Astropy v7.1)"). If no radius is specified, it defaults to 1
arcmin. Another optional parameter is the equinox if coordinates are
specified. By default this is J2000.0 but can also be set to B1950.0.

```
>>> from astroquery.ipac.ned import Ned
>>> import astropy.units as u
>>> result_table = Ned.query_region("3c 273", radius=0.05 * u.deg)
>>> print(result_table)
No.        Object Name             RA     ... Diameter Points Associations
                                degrees   ...
--- -------------------------- ---------- ... --------------- ------------
  1 SSTSL2 J122855.02+020313.7  187.22925 ...               0            0
  2  WISEA J122855.03+020309.1  187.22925 ...               0            0
  3 SSTSL2 J122855.23+020341.5  187.23013 ...               0            0
  4 SSTSL2 J122855.36+020346.9  187.23068 ...               0            0
...                        ...        ... ...             ...          ...
864 SSTSL2 J122918.24+020330.7    187.326 ...               0            0
865   SDSS J122918.38+020323.4   187.3266 ...               4            0
866 SSTSL2 J122918.52+020338.9  187.32718 ...               0            0
867 SSTSL2 J122918.64+020326.7  187.32767 ...               0            0
Length = 867 rows
```

Instead of using the name, the target may also be specified via
coordinates. Any of the coordinate systems available in [`astropy.coordinates`](https://docs.astropy.org/en/stable/coordinates/ref_api.html#module-astropy.coordinates "(in Astropy v7.1)")
may be used (ICRS, Galactic, FK4, FK5). Note also the use of the equinox keyword argument:

```
>>> from astroquery.ipac.ned import Ned
>>> import astropy.units as u
>>> from astropy import coordinates
>>> co = coordinates.SkyCoord(ra=56.38, dec=38.43,
...                           unit=(u.deg, u.deg), frame='fk4')
>>> result_table = Ned.query_region(co, radius=0.1 * u.deg, equinox='B1950.0')
>>> print(result_table)
No.        Object Name            RA     ... Diameter Points Associations
                               degrees   ...
--- ------------------------- ---------- ... --------------- ------------
  1 WISEA J035137.90+384313.7   57.90793 ...               0            0
  2 WISEA J035138.59+384305.6   57.91081 ...               0            0
  3 WISEA J035139.28+384324.4   57.91371 ...               0            0
  4 WISEA J035139.77+384507.4   57.91572 ...               0            0
...                       ...        ... ...             ...          ...
631 WISEA J035237.78+384519.3   58.15743 ...               0            0
632 WISEA J035238.62+384431.9   58.16083 ...               0            0
633 WISEA J035238.74+384352.1   58.16145 ...               0            0
634 WISEA J035238.84+384437.0   58.16177 ...               0            0
Length = 634 rows
```

#### Query in the IAU format

The [IAU format](https://cds.unistra.fr/Dic/iau-spec.html) for coordinates may also be used for querying
purposes. Additional parameters that can be specified for these queries is the
reference frame of the coordinates. The reference frame defaults to
`Equatorial`. But it can also take the values `Ecliptic`, `Galactic` and
`SuperGalactic`. The equinox can also be explicitly chosen (same as in region
queries). It defaults to `B1950` but again it may be set to `J2000.0`. Note
that Ned report results by searching in a 15 arcmin radius around the specified
target.

```
>>> from astroquery.ipac.ned import Ned
>>> result_table = Ned.query_region_iau('1234-423', frame='SuperGalactic', equinox='J2000.0')
>>> print(result_table)
No.        Object Name            RA     ... Diameter Points Associations
                               degrees   ...
--- ------------------------- ---------- ... --------------- ------------
  1 WISEA J123639.37-423822.9  189.16406 ...               0            0
  2 WISEA J123639.47-423656.3  189.16458 ...               0            0
  3 WISEA J123639.61-423637.9  189.16504 ...               0            0
  4 WISEA J123639.91-423709.9   189.1663 ...               0            0
...                       ...        ... ...             ...          ...
760   2MASS J12374631-4236174  189.44299 ...               0            0
761 WISEA J123746.44-423727.9  189.44353 ...               0            0
762 WISEA J123746.48-423838.1   189.4437 ...               0            0
763 WISEA J123747.07-423742.9  189.44616 ...               0            0
Length = 763 rows
```

#### Query a reference code for objects

These queries can be used to retrieve all objects that appear in the specified
19 digit reference code. These are similar to the
[`query_bibobj()`](../../api/astroquery.simbad.SimbadClass.html#astroquery.simbad.SimbadClass.query_bibobj "astroquery.simbad.SimbadClass.query_bibobj") queries.

```
>>> from astroquery.ipac.ned import Ned
>>> result_table = Ned.query_refcode('1997A&A...323...31K')
>>> print(result_table)
No.        Object Name            RA     ... Diameter Points Associations
                               degrees   ...
--- ------------------------- ---------- ... --------------- ------------
  1                  NGC 0262   12.19642 ...              12            0
  2                  NGC 0449      19.03 ...               7            0
  3                  NGC 0591   23.38016 ...               7            0
  4                 UGC 01214   25.99076 ...              12            0
...                       ...        ... ...             ...          ...
 33 WISEA J202325.39+113134.6   305.8558 ...               2            0
 34                 UGC 12149  340.28164 ...               8            0
 35                  MRK 0522  345.07958 ...               4            0
 36                  NGC 7674  351.98626 ...               8            0
 Length = 36 rows
```

#### Image and Spectra Queries

The image queries return a list of [`HDUList`](https://docs.astropy.org/en/stable/io/fits/api/hdulists.html#astropy.io.fits.HDUList "(in Astropy v7.1)") objects for the
specified name. For instance:

```
>>> from astroquery.ipac.ned import Ned
>>> images = Ned.get_images("m1")
Downloading https://ned.ipac.caltech.edu/dss1B2/Bb/MESSIER_001:I:103aE:dss1.fits.gz
|===========================================|  32k/ 32k (100.00%)        00s
Downloading https://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p083n22a:I:0.1-2.4keV:cop1995.fits.gz
|===========================================|  52k/ 52k (100.00%)        01s
Downloading https://ned.ipac.caltech.edu/img5/1996RXCD6.T...0000C/p083n22a:I:0.1-2.4keV:cps1996.fits.gz
|===========================================|  96k/ 96k (100.00%)        03s
Downloading https://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p084n22a:I:0.1-2.4keV:cop1995.fits.gz
|===========================================|  52k/ 52k (100.00%)        01s
Downloading https://ned.ipac.caltech.edu/img5/1998RXCD8.T...0000C/h083n22a:I:0.1-2.4keV:cps1998.fits.gz
|===========================================|  35k/ 35k (100.00%)        00s
>>> images
[[<astropy.io.fits.hdu.image.PrimaryHDU at 0x4311890>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x432b350>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x3e9c5d0>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x4339790>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x433dd90>]]
```

To get the URLs of the downloadable FITS images:

```
>>> from astroquery.ipac.ned import Ned
>>> image_list = Ned.get_image_list("m1")
>>> image_list
['https://ned.ipac.caltech.edu/dss1B2/Bb/MESSIER_001:I:103aE:dss1.fits.gz',
 'https://ned.ipac.caltech.edu/img/1995RXCD3.T...0000C/p084n22a:I:0.1-2.4keV:cop1995.fits.gz',
 'https://ned.ipac.caltech.edu/img/1996RXCD6.T...0000C/p083n22a:I:0.1-2.4keV:cps1996.fits.gz',
 'https://ned.ipac.caltech.edu/img/1998RXCD8.T...0000C/h083n22a:I:0.1-2.4keV:cps1998.fits.gz',
 'https://ned.ipac.caltech.edu/img/1995RXCD3.T...0000C/p083n22a:I:0.1-2.4keV:cop1995.fits.gz']
```

Spectra can also be fetched in the same way:

```
>>> from astroquery.ipac.ned import Ned
>>> spectra = Ned.get_spectra('3c 273')
Downloading https://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:B:bcc2009.fits.gz
|===========================================| 7.8k/7.8k (100.00%)        00s
Downloading https://ned.ipac.caltech.edu/spc1/1992ApJS...80..109B/PG_1226+023:S:B_V:bg1992.fits.gz
|===========================================| 5.0k/5.0k (100.00%)        00s
Downloading https://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:RI:bcc2009.fits.gz
|===========================================| 9.4k/9.4k (100.00%)        00s
>>> spectra
[[<astropy.io.fits.hdu.image.PrimaryHDU at 0x41b4190>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x41b0990>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x430a450>]]
```

Similarly the list of URLs for spectra of a particular object may be fetched:

```
>>> from astroquery.ipac.ned import Ned
>>> spectra_list = Ned.get_image_list("3c 273", item='spectra')
>>> spectra_list
['https://ned.ipac.caltech.edu/spc1/1992/1992ApJS...80..109B/PG_1226+023:S:B_V:bg1992.fits.gz',
 'https://ned.ipac.caltech.edu/spc1/2009/2009A+A...495.1033B/3C_273:S:B:bcc2009.fits.gz',
 ...
 'https://ned.ipac.caltech.edu/spc1/2016/2016ApJS..226...19F/3C_273:S:CII158.3x3.fits.gz']
```