# IRSA Image Server program interface (IBE) Queries ([`astroquery.ipac.irsa.ibe`](#module-astroquery.ipac.irsa.ibe "astroquery.ipac.irsa.ibe"))

This module can has methods to perform different types of queries on the
catalogs present in the IRSA Image Server program interface (IBE), which
currently provides access to the 2MASS, WISE, and PTF image archives. In
addition to supporting the standard query methods
[`query_region()`](../../../api/astroquery.ipac.irsa.ibe.IbeClass.html#astroquery.ipac.irsa.ibe.IbeClass.query_region "astroquery.ipac.irsa.ibe.IbeClass.query_region") and
[`query_region_async()`](../../../api/astroquery.ipac.irsa.ibe.IbeClass.html#astroquery.ipac.irsa.ibe.IbeClass.query_region_async "astroquery.ipac.irsa.ibe.IbeClass.query_region_async"), there are also methods to
query the available missions ([`list_missions()`](../../../api/astroquery.ipac.irsa.ibe.IbeClass.html#astroquery.ipac.irsa.ibe.IbeClass.list_missions "astroquery.ipac.irsa.ibe.IbeClass.list_missions")), datasets ([`list_datasets()`](../../../api/astroquery.ipac.irsa.ibe.IbeClass.html#astroquery.ipac.irsa.ibe.IbeClass.list_datasets "astroquery.ipac.irsa.ibe.IbeClass.list_datasets")), tables ([`list_tables()`](../../../api/astroquery.ipac.irsa.ibe.IbeClass.html#astroquery.ipac.irsa.ibe.IbeClass.list_tables "astroquery.ipac.irsa.ibe.IbeClass.list_tables")), and columns ([`get_columns()`](../../../api/astroquery.ipac.irsa.ibe.IbeClass.html#astroquery.ipac.irsa.ibe.IbeClass.get_columns "astroquery.ipac.irsa.ibe.IbeClass.get_columns")).

## Troubleshooting

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

```
>>> from astroquery.ipac.irsa.ibe import Ibe
>>> Ibe.clear_cache()
```

If this function is unavailable, upgrade your version of astroquery.
The `clear_cache` function was introduced in version 0.4.7.dev8479.

## Reference/API

### astroquery.ipac.irsa.ibe Package