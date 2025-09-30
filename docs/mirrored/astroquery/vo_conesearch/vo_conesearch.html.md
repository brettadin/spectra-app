# VO Simple Cone Search (`astroquery.vo_conesearch`)

Astroquery offers Simple Cone Search Version 1.03 as defined in IVOA
Recommendation (February 22, 2008). Cone Search queries an
area encompassed by a given radius centered on a given RA and Dec and returns
all the objects found within the area in the given catalog.

This was ported from `astropy.vo`:

`astroquery.vo_conesearch.ConeSearch` is a Cone Search API that adheres to
Astroquery standards but unlike Astropy’s version, it only queries one given
service URL, which defaults to HST Guide Star Catalog. This default is
controlled by `astroquery.vo_conesearch.conf.fallback_url`.

## Default Cone Search Services

For the “classic” API ported from Astropy, the default Cone Search services
used are a subset of those found in the STScI VAO Registry.
They were hand-picked to represent commonly used catalogs below:

This subset undergoes daily validations hosted by STScI using
[Validation for Simple Cone Search](validator.html#vo-sec-validator-validate). Those that pass without critical
warnings or exceptions are used by [Simple Cone Search](client.html#vo-sec-client-scs) by
default. They are controlled by
`astroquery.vo_conesearch.conf.conesearch_dbname`:

1. `'conesearch_good'`
   Default. Passed validation without critical warnings and exceptions.
2. `'conesearch_warn'`
   Has critical warnings but no exceptions. Use at your own risk.
3. `'conesearch_exception'`
   Has some exceptions. *Never* use this.
4. `'conesearch_error'`
   Has network connection error. *Never* use this.

If you are a Cone Search service provider and would like to include your
service in the list above, please open a
[GitHub issue on Astroquery](https://github.com/astropy/astroquery/issues).

## Caching

Caching of downloaded contents is controlled by [`astropy.utils.data`](https://docs.astropy.org/en/stable/utils/ref_api.html#module-astropy.utils.data "(in Astropy v7.1)").
To use cached data, some functions in this package have a `cache`
keyword that can be set to `True`.

## Getting Started

This section only contains minimal examples showing how to perform
basic Cone Search.

Query STScI Guide Star Catalog using “new” Astroquery-style API
around M31 with a 0.1-degree search radius:

```
>>> from astropy.coordinates import SkyCoord
>>> from astroquery.vo_conesearch import ConeSearch
>>> c = SkyCoord.from_name('M31')
>>> c
<SkyCoord (ICRS): (ra, dec) in deg
    (10.6847083, 41.26875)>
>>> result = ConeSearch.query_region(c, '0.1 deg')
>>> result
<Table length=4028>
    objID           gsc2ID      gsc1ID ... multipleFlag compassGSC2id   Mag
                                       ...                              mag
    int64           object      object ...    int32         int64     float32
-------------- ---------------- ------ ... ------------ ------------- -------
23323175812944 00424433+4116085        ...            0 6453800072293   9.453
23323175812948 00424403+4116069        ...            0 6453800072297   9.321
23323175812933 00424455+4116103        ...            0 6453800072282  10.773
23323175812939 00424464+4116092        ...            0 6453800072288   9.299
23323175812930 00424403+4116108        ...            0 6453800072279  11.507
23323175812931 00424464+4116106        ...            0 6453800072280   9.399
           ...              ...    ... ...          ...           ...     ...
  133001227000     N33001227000        ...            0 6453800007000 20.1382
 1330012244001    N330012244001        ...            0 6453800044001 21.8968
 1330012228861    N330012228861        ...            0 6453800028861 20.3572
 1330012212014    N330012212014        ...            0 6453800012014 16.5079
 1330012231849    N330012231849        ...            0 6453800031849 20.2869
 1330012210212    N330012210212        ...            0 6453800010212 20.2767
>>> result.url
'http://gsss.stsci.edu/webservices/vo/ConeSearch.aspx?CAT=GSC23'
```

List the available Cone Search catalogs that passed daily validation:

```
>>> from astroquery.vo_conesearch import conesearch
>>> conesearch.list_catalogs()
Downloading https://astroconda.org/aux/vo_databases/conesearch_good.json
|==========================================|  59k/ 59k (100.00%)         0s
['Guide Star Catalog 2.3 Cone Search 1',
 'SDSS DR7 - Sloan Digital Sky Survey Data Release 7 1',
 'SDSS DR7 - Sloan Digital Sky Survey Data Release 7 2', ...,
 'Two Micron All Sky Survey (2MASS) 2']
```

Query the HST Guide Star Catalog around M31 with a 0.1-degree search radius.
This is the same query as above but using “classic” Astropy-style API:

```
>>> from astropy import units as u
>>> my_catname = 'Guide Star Catalog 2.3 Cone Search 1'
>>> result = conesearch.conesearch(c, 0.1 * u.degree, catalog_db=my_catname)
Trying http://gsss.stsci.edu/webservices/vo/ConeSearch.aspx?CAT=GSC23&
WARNING: W50: ...: Invalid unit string 'pixel' [...]
>>> result
<Table length=4028>
    objID           gsc2ID      gsc1ID ... multipleFlag compassGSC2id   Mag
                                       ...                              mag
    int64           object      object ...    int32         int64     float32
-------------- ---------------- ------ ... ------------ ------------- -------
23323175812944 00424433+4116085        ...            0 6453800072293   9.453
23323175812948 00424403+4116069        ...            0 6453800072297   9.321
23323175812933 00424455+4116103        ...            0 6453800072282  10.773
23323175812939 00424464+4116092        ...            0 6453800072288   9.299
23323175812930 00424403+4116108        ...            0 6453800072279  11.507
23323175812931 00424464+4116106        ...            0 6453800072280   9.399
           ...              ...    ... ...          ...           ...     ...
  133001227000     N33001227000        ...            0 6453800007000 20.1382
 1330012244001    N330012244001        ...            0 6453800044001 21.8968
 1330012228861    N330012228861        ...            0 6453800028861 20.3572
 1330012212014    N330012212014        ...            0 6453800012014 16.5079
 1330012231849    N330012231849        ...            0 6453800031849 20.2869
 1330012210212    N330012210212        ...            0 6453800010212 20.2767
>>> result.url
'http://gsss.stsci.edu/webservices/vo/ConeSearch.aspx?CAT=GSC23'
```

Get the number of matches and returned column names:

```
>>> len(result)
4028
>>> result.colnames
['objID',
 'gsc2ID',
 'gsc1ID',
 'hstID',
 'ra',
 'dec', ...,
 'Mag']
```

Extract RA and Dec of the matches:

```
>>> result_skycoord = SkyCoord(result['ra'], result['dec'])
>>> result_skycoord
<SkyCoord (ICRS): (ra, dec) in deg
    [(10.684737  , 41.269035  ), (10.683469  , 41.268585  ),
     (10.685657  , 41.26955   ), ..., (10.58375359, 41.33386612),
     (10.55860996, 41.30061722), (10.817729  , 41.26915741)]>
```

## Using `astroquery.vo_conesearch`

This package has four main components across two categories:

They are designed to be used in a work flow as illustrated below:

[![VO work flow](../_images/astroquery_vo_flowchart.png)](../_images/astroquery_vo_flowchart.png)

The one that a typical user needs is the [Simple Cone Search](client.html#vo-sec-client-scs) component
(see [Cone Search Examples](client.html#vo-sec-scs-examples)).

## Troubleshooting

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

```
>>> from astroquery.vo_conesearch import ConeSearch
>>> ConeSearch.clear_cache()
```

If this function is unavailable, upgrade your version of astroquery.
The `clear_cache` function was introduced in version 0.4.7.dev8479.

## Reference/API

### astroquery.vo\_conesearch.core Module

#### Classes

|  |  |
| --- | --- |
| [`ConeSearchClass`](../api/astroquery.vo_conesearch.core.ConeSearchClass.html#astroquery.vo_conesearch.core.ConeSearchClass "astroquery.vo_conesearch.core.ConeSearchClass")() | The class for querying the Virtual Observatory (VO) Cone Search web service. |

#### Class Inheritance Diagram

Inheritance diagram of astroquery.vo\_conesearch.core.ConeSearchClass

### astroquery.vo\_conesearch.vos\_catalog Module

Common utilities for accessing VO simple services.

Note

Some functions are not used by Astroquery but kept for
backward-compatibility with `astropy.vo.client`.

#### Functions

|  |  |
| --- | --- |
| [`get_remote_catalog_db`](../api/astroquery.vo_conesearch.vos_catalog.get_remote_catalog_db.html#astroquery.vo_conesearch.vos_catalog.get_remote_catalog_db "astroquery.vo_conesearch.vos_catalog.get_remote_catalog_db")(dbname, \*[, cache, ...]) | Get a database of VO services (which is a JSON file) from a remote location. |
| [`call_vo_service`](../api/astroquery.vo_conesearch.vos_catalog.call_vo_service.html#astroquery.vo_conesearch.vos_catalog.call_vo_service "astroquery.vo_conesearch.vos_catalog.call_vo_service")(service\_type[, catalog\_db, ...]) | Makes a generic VO service call. |
| [`list_catalogs`](../api/astroquery.vo_conesearch.vos_catalog.list_catalogs.html#astroquery.vo_conesearch.vos_catalog.list_catalogs "astroquery.vo_conesearch.vos_catalog.list_catalogs")(service\_type[, cache, verbose]) | List the catalogs available for the given service type. |

### astroquery.vo\_conesearch.conesearch Module

Support VO Simple Cone Search capabilities.

#### Functions

|  |  |
| --- | --- |
| [`conesearch`](../api/astroquery.vo_conesearch.conesearch.conesearch.html#astroquery.vo_conesearch.conesearch.conesearch "astroquery.vo_conesearch.conesearch.conesearch")(center, radius, \*[, verb, ...]) | Perform Cone Search and returns the result of the first successful query. |
| [`search_all`](../api/astroquery.vo_conesearch.conesearch.search_all.html#astroquery.vo_conesearch.conesearch.search_all "astroquery.vo_conesearch.conesearch.search_all")(\*args, \*\*kwargs) | Perform Cone Search and returns the results of all successful queries. |
| [`list_catalogs`](../api/astroquery.vo_conesearch.conesearch.list_catalogs.html#astroquery.vo_conesearch.conesearch.list_catalogs "astroquery.vo_conesearch.conesearch.list_catalogs")(\*\*kwargs) | Return the available Cone Search catalogs as a list of strings. |
| [`predict_search`](../api/astroquery.vo_conesearch.conesearch.predict_search.html#astroquery.vo_conesearch.conesearch.predict_search "astroquery.vo_conesearch.conesearch.predict_search")(url, \*args, \*\*kwargs) | Predict the run time needed and the number of objects for a Cone Search for the given access URL, position, and radius. |
| [`conesearch_timer`](../api/astroquery.vo_conesearch.conesearch.conesearch_timer.html#astroquery.vo_conesearch.conesearch.conesearch_timer "astroquery.vo_conesearch.conesearch.conesearch_timer")(\*args, \*\*kwargs) | Time a single Cone Search using [`astroquery.utils.timer.timefunc`](../api/astroquery.utils.timer.timefunc.html#astroquery.utils.timer.timefunc "astroquery.utils.timer.timefunc") with a single try and a verbose timer. |

#### Classes

|  |  |
| --- | --- |
| [`AsyncConeSearch`](../api/astroquery.vo_conesearch.conesearch.AsyncConeSearch.html#astroquery.vo_conesearch.conesearch.AsyncConeSearch "astroquery.vo_conesearch.conesearch.AsyncConeSearch")(\*args, \*\*kwargs) | Perform a Cone Search asynchronously and returns the result of the first successful query. |
| [`AsyncSearchAll`](../api/astroquery.vo_conesearch.conesearch.AsyncSearchAll.html#astroquery.vo_conesearch.conesearch.AsyncSearchAll "astroquery.vo_conesearch.conesearch.AsyncSearchAll")(\*args, \*\*kwargs) | Perform a Cone Search asynchronously, storing all results instead of just the result from first successful query. |

### astroquery.vo\_conesearch.vo\_async Module

Asynchronous VO service requests.

### astroquery.vo\_conesearch.exceptions Module

Exceptions related to Virtual Observatory (VO).

#### Class Inheritance Diagram

Inheritance diagram of astroquery.vo\_conesearch.exceptions.BaseVOError, astroquery.vo\_conesearch.exceptions.VOSError, astroquery.vo\_conesearch.exceptions.MissingCatalog, astroquery.vo\_conesearch.exceptions.DuplicateCatalogName, astroquery.vo\_conesearch.exceptions.DuplicateCatalogURL, astroquery.vo\_conesearch.exceptions.InvalidAccessURL, astroquery.vo\_conesearch.exceptions.ConeSearchError

### astroquery.vo\_conesearch.validator.validate Module

Validate VO Services.

### astroquery.vo\_conesearch.validator.exceptions Module

Exceptions related to Virtual Observatory (VO) validation.

#### Class Inheritance Diagram

Inheritance diagram of astroquery.vo\_conesearch.validator.exceptions.BaseVOValidationError, astroquery.vo\_conesearch.validator.exceptions.ValidationMultiprocessingError