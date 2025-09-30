#### Query by an Identifier

This is useful if you want to query an object by a known identifier (name). For instance
to query the messier object M1:

```
>>> from astroquery.simbad import Simbad
>>> result_table = Simbad.query_object("m1")
>>> print(result_table)
main_id    ra     dec   ... coo_wavelength     coo_bibcode     matched_id
          deg     deg   ...
------- ------- ------- ... -------------- ------------------- ----------
  M   1 83.6324 22.0174 ...              X 2022A&A...661A..38P      M   1
```

[Wildcards](#wildcards) are supported. Note that this makes the query case-sensitive.
This allows, for instance, to query messier objects from 1 through 9:

```
>>> from astroquery.simbad import Simbad
>>> result_table = Simbad.query_object("M [1-9]", wildcard=True)
>>> print(result_table)
 main_id          ra         ...     coo_bibcode     matched_id
                 deg         ...
--------- ------------------ ... ------------------- ----------
    M   1            83.6287 ... 1995AuJPh..48..143S      M   1
    M   2 323.36258333333336 ... 2010AJ....140.1830G      M   2
    M   3  205.5484166666666 ... 2010AJ....140.1830G      M   3
NGC  6475 268.44699999999995 ... 2021A&A...647A..19T      M   7
NGC  6405 265.06899999999996 ... 2021A&A...647A..19T      M   6
    M   4 245.89675000000003 ... 2010AJ....140.1830G      M   4
    M   8 270.90416666666664 ...                          M   8
    M   9 259.79908333333333 ... 2002MNRAS.332..441F      M   9
    M   5 229.63841666666673 ... 2010AJ....140.1830G      M   5
```

The messier objects from 1 to 9 are found. Their main identifier `main_id` is not
necessarily the one corresponding to the wildcard expression.
The column `matched_id` contains the identifier that was matched.

Note that in this example, the wildcard parameter could have been replaced by a way
faster query done with [`query_objects`](../api/astroquery.simbad.SimbadClass.html#astroquery.simbad.SimbadClass.query_objects "astroquery.simbad.SimbadClass.query_objects").

##### Wildcards

Wildcards are supported in these methods:

They allow to provide a pattern that the query will match. To see the available
wildcards and their meaning:

```
>>> from astroquery.simbad import Simbad
>>> Simbad().list_wildcards()
*: Any string of characters (including an empty one)
?: Any character (exactly one character)
[abc]: Exactly one character taken in the list. Can also be defined by a range of characters: [A-Z]
[^0-9]: Any (one) character not in the list.
```

#### Query hierarchy: to get all parents (or children, or siblings) of an object

SIMBAD also records hierarchy links between objects. For example, two galaxies in a pair
of galaxies are siblings, a cluster of stars is composed of stars: its children. This
information can be accessed with the [`query_hierarchy`](../api/astroquery.simbad.SimbadClass.html#astroquery.simbad.SimbadClass.query_hierarchy "astroquery.simbad.SimbadClass.query_hierarchy")
method.

Whenever available, membership probabilities are recorded in SIMBAD as given by
the authors, though rounded to an integer. When authors do not give a value but
assessments, they are translated in SIMBAD as follows:

| assessment | membership certainty |
| --- | --- |
| member | 100 |
| likely member | 75 |
| possible member | 50 |
| likely not member | 25 |
| non member | 0 |

For gravitational lens systems, double stars, and blends (superposition of two
non-physically linked objects), the SIMBAD team does not assign a probability
value (this will be a `None`).

You can find more details in the [hierarchy documentation](https://simbad.cds.unistra.fr/guide/dataHierarchy.htx) of SIMBAD’s webpages.

Let’s find the galaxies composing the galaxy pair `Mrk 116`:

```
>>> from astroquery.simbad import Simbad
>>> galaxies = Simbad.query_hierarchy("Mrk 116",
...                                   hierarchy="children", criteria="otype='G..'")
>>> galaxies[["main_id", "ra", "dec", "membership_certainty"]]
<Table length=2>
 main_id         ra            dec       membership_certainty
                deg            deg             percent
  object      float64        float64            int16
--------- --------------- -------------- --------------------
Mrk  116A 143.50821525019 55.24105273196                   --
Mrk  116B      143.509956      55.239762                   --
```

Alternatively, if we know one member of a group, we can find the others by asking for
`siblings`:

```
>>> from astroquery.simbad import Simbad
>>> galaxies = Simbad.query_hierarchy("Mrk 116A",
...                                   hierarchy="siblings", criteria="otype='G..'")
>>> galaxies[["main_id", "ra", "dec", "membership_certainty"]]
<Table length=2>
 main_id         ra            dec       membership_certainty
                deg            deg             percent
  object      float64        float64            int16
--------- --------------- -------------- --------------------
Mrk  116A 143.50821525019 55.24105273196                   --
Mrk  116B      143.509956      55.239762                   --
```

Note that if we had not added the criteria on the object type, we would also get
some stars that are part of these galaxies in the result.

And the other way around, let’s find which cluster of stars contains
`2MASS J18511048-0615470`:

```
>>> from astroquery.simbad import Simbad
>>> cluster = Simbad.query_hierarchy("2MASS J18511048-0615470",
...                                  hierarchy="parents", detailed_hierarchy=False)
>>> cluster[["main_id", "ra", "dec"]]
<Table length=1>
 main_id     ra     dec
            deg     deg
  object  float64 float64
--------- ------- -------
NGC  6705 282.766  -6.272
```

By default, we get a more detailed report with the two extra columns:
:   * `hierarchy_bibcode` : the paper in which the hierarchy is established,
    * `membership_certainty`: if present in the paper, a certainty index (100 meaning
      100% sure).

```
>>> from astroquery.simbad import Simbad
>>> cluster = Simbad.query_hierarchy("2MASS J18511048-0615470",
...                                  hierarchy="parents",
...                                  detailed_hierarchy=True)
>>> cluster[["main_id", "ra", "dec", "hierarchy_bibcode", "membership_certainty"]]
<Table length=13>
 main_id     ra     dec    hierarchy_bibcode  membership_certainty
            deg     deg                             percent
  object  float64 float64        object              int16
--------- ------- ------- ------------------- --------------------
NGC  6705 282.766  -6.272 2014A&A...563A..44M                  100
NGC  6705 282.766  -6.272 2015A&A...573A..55T                  100
NGC  6705 282.766  -6.272 2016A&A...591A..37J                  100
NGC  6705 282.766  -6.272 2018A&A...618A..93C                  100
NGC  6705 282.766  -6.272 2020A&A...633A..99C                  100
NGC  6705 282.766  -6.272 2020A&A...640A...1C                  100
NGC  6705 282.766  -6.272 2020A&A...643A..71G                  100
NGC  6705 282.766  -6.272 2020ApJ...903...55P                  100
NGC  6705 282.766  -6.272 2020MNRAS.496.4701J                  100
NGC  6705 282.766  -6.272 2021A&A...647A..19T                  100
NGC  6705 282.766  -6.272 2021A&A...651A..84M                  100
NGC  6705 282.766  -6.272 2021MNRAS.503.3279S                   99
NGC  6705 282.766  -6.272 2022MNRAS.509.1664J                  100
```

Here, we see that the SIMBAD team found 13 papers mentioning the fact that
`2MASS J18511048-0615470` is a member of `NGC  6705` and that the authors of these
articles gave high confidence indices for this membership (`membership_certainty` is
close to 100 for all bibcodes).

##### A note of caution on hierarchy

In some tricky cases, low membership values represent extremely important information.
Let’s for example look at the star `V* V787 Cep`:

```
>>> from astroquery.simbad import Simbad
>>> parents = Simbad.query_hierarchy("V* V787 Cep",
...                                  hierarchy="parents",
...                                  detailed_hierarchy=True)
>>> parents[["main_id", "ra", "dec", "hierarchy_bibcode", "membership_certainty"]]
<Table length=4>
 main_id          ra           dec    hierarchy_bibcode  membership_certainty
                 deg           deg                             percent
  object       float64       float64        object              int16
--------- ------------------ ------- ------------------- --------------------
NGC   188 11.797999999999998  85.244 2003AJ....126.2922P                   46
NGC   188 11.797999999999998  85.244 2004PASP..116.1012S                   46
NGC   188 11.797999999999998  85.244 2018A&A...616A..10G                  100
NGC   188 11.797999999999998  85.244 2021MNRAS.503.3279S                    1
```

Here, we see that the link between `V* V787 Cep` and the open cluster `NGC 188` is
opened for debate: the only way to build an opinion is to read the four articles.
This information would be hidden if we did not print the detailed hierarchy report.

These somewhat contradictory results are an inherent part of SIMBAD, which simply
translates the literature into a database.

#### Query a region

Query in a cone with a specified radius. The center can be a string with an
identifier, a string representing coordinates, or a [`SkyCoord`](https://docs.astropy.org/en/stable/api/astropy.coordinates.SkyCoord.html#astropy.coordinates.SkyCoord "(in Astropy v7.1)").

```
>>> from astroquery.simbad import Simbad
>>> # get 10 objects in a radius of 0.5° around M81
>>> simbad = Simbad()
>>> simbad.ROW_LIMIT = 10
>>> result_table = simbad.query_region("m81", radius="0.5d")
>>> print(result_table)
             main_id                       ra                dec        ... coo_err_angle coo_wavelength     coo_bibcode
                                          deg                deg        ...      deg
---------------------------------- ------------------ ----------------- ... ------------- -------------- -------------------
                      [PR95] 40298 149.14159166666667 69.19170000000001 ...            --
                       [GTK91b] 19 149.03841666666668 69.21222222222222 ...            --
                       [GTK91b] 15 149.26095833333332 69.22230555555556 ...            --
                           PSK 212 148.86083333333332 69.15333333333334 ...            --
                           PSK 210  148.8595833333333 69.20111111111112 ...            --
                       [BBC91] N06 148.84166666666664 69.14222222222223 ...            --
[GKP2011] M81C J095534.66+691213.7 148.89441666666667 69.20380555555556 ...            --              O 2011ApJ...743..176G
                      [PR95] 51153 148.89568749999998  69.1995888888889 ...            --              O 2012ApJ...747...15K
                           PSK 300 148.96499999999997 69.16638888888889 ...            --
                           PSK 234  148.9008333333333 69.19944444444445 ...            --
```

When no radius is specified, the radius defaults to 2 arcmin. When the radius is
explicitly specified it can be either a string accepted by
[`Angle`](https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html#astropy.coordinates.Angle "(in Astropy v7.1)") (ex: `radius='0d6m0s'`) or directly a
[`Quantity`](https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity "(in Astropy v7.1)") object.

If the center is defined by coordinates, then the best solution is to use a
[`astropy.coordinates.SkyCoord`](https://docs.astropy.org/en/stable/api/astropy.coordinates.SkyCoord.html#astropy.coordinates.SkyCoord "(in Astropy v7.1)") object.

```
>>> from astroquery.simbad import Simbad
>>> from astropy.coordinates import SkyCoord
>>> import astropy.units as u
>>> Simbad.query_region(SkyCoord(31.0087, 14.0627, unit=(u.deg, u.deg),
...                     frame='galactic'), radius=2 * u.arcsec)
<Table length=2>
       main_id                ra        ... coo_wavelength     coo_bibcode
                             deg        ...
        object             float64      ...      str1             object
--------------------- ----------------- ... -------------- -------------------
NAME Barnard's Star b 269.4520769586187 ...              O 2020yCat.1350....0G
  NAME Barnard's star 269.4520769586187 ...              O 2020yCat.1350....0G
```

Note

Calling [`query_region`](../api/astroquery.simbad.SimbadClass.html#astroquery.simbad.SimbadClass.query_region "astroquery.simbad.SimbadClass.query_region") within a loop is **very**
inefficient. If you need to query many regions, use a multi-coordinate
[`SkyCoord`](https://docs.astropy.org/en/stable/api/astropy.coordinates.SkyCoord.html#astropy.coordinates.SkyCoord "(in Astropy v7.1)") and a list of radii. It looks like this:

```
>>> from astroquery.simbad import Simbad
>>> from astropy.coordinates import SkyCoord
>>> import astropy.units as u
>>> Simbad.query_region(SkyCoord(ra=[10, 11], dec=[10, 11],
...                     unit=(u.deg, u.deg), frame='fk5'),
...                     radius=[0.1 * u.deg, 2* u.arcmin])
<Table length=6>
        main_id                  ra         ...     coo_bibcode
                                deg         ...
         object               float64       ...        object
------------------------ ------------------ ... -------------------
SDSS J004014.26+095527.0 10.059442999999998 ... 2020ApJS..250....8L
            LEDA 1387229 10.988333333333335 ... 2003A&A...412...45P
         IRAS 00371+0946   9.92962860161661 ... 1988NASAR1190....1B
         IRAS 00373+0947  9.981768085280164 ... 1988NASAR1190....1B
   PLCKECC G118.25-52.70  9.981250000000001 ... 2011A&A...536A...7P
  GALEX J004011.0+095752 10.045982309580001 ... 2020yCat.1350....0G
```

If the radius is the same in every cone, you can also just give this single radius without
having to create the list (ex: `radius = "5arcmin"`).

#### Query a catalogue

Queries can also return all the objects from a catalogue. For instance to query
the ESO catalog:

```
>>> from astroquery.simbad import Simbad
>>> simbad = Simbad(ROW_LIMIT=6)
>>> simbad.query_catalog('ESO')
<Table length=6>
 main_id          ra         ...     coo_bibcode     catalog_id
                 deg         ...
  object       float64       ...        object         object
--------- ------------------ ... ------------------- ----------
NGC  2573     25.40834109527 ... 2020yCat.1350....0G  ESO   1-1
ESO   1-2           76.15327 ... 2020MNRAS.494.1784A  ESO   1-2
ESO   1-3  80.65212083333333 ... 2006AJ....131.1163S  ESO   1-3
ESO   1-4 117.37006325383999 ... 2020yCat.1350....0G  ESO   1-4
ESO   1-5  133.2708583333333 ... 2006AJ....131.1163S  ESO   1-5
ESO   1-6    216.83122280179 ... 2020yCat.1350....0G  ESO   1-6
```

Note that the name in `main_id` is not necessarily from the queried catalog. This
information is in the `catalog_id` column.

To see the available catalogues, you can write a custom ADQL query
(see [query\_tap](#query-tap-documentation).) on the `cat` table.
For example to get the 10 biggest catalogs in SIMBAD, it looks like this:

```
>>> from astroquery.simbad import Simbad
>>> Simbad.query_tap('SELECT TOP 10 cat_name, description FROM cat ORDER BY "size" DESC')
<Table length=10>
cat_name                           description
object                               object
-------- ----------------------------------------------------------------
    Gaia                                                             Gaia
   2MASS                               2 Micron Sky Survey, Point Sources
     TIC                                               TESS Input Catalog
    SDSS                                         Sloan Digital Sky Survey
     TYC                                                    Tycho mission
    OGLE                              Optical Gravitational Lensing Event
   UCAC4                               Fourth USNO CCD Astrograph Catalog
    WISE Wide-field Infrared Survey Explorer Final Release Source Catalog
     GSC                                             Guide Star Catalogue
    LEDA                              Lyon-Meudon Extragalactic DatabaseA
```

Where you can remove `TOP 10` to get **all** the catalogues (there’s a lot of them).

Warning

This method is case-sensitive since version 0.4.8