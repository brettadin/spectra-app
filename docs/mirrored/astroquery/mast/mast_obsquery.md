## Observation Criteria Queries

To search for observations based on parameters other than position or target name,
use [`query_criteria`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.query_criteria "astroquery.mast.ObservationsClass.query_criteria").
Criteria are supplied as keyword arguments, where valid criteria are “coordinates”,
“objectname”, “radius” (as in [`query_region`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.query_region "astroquery.mast.ObservationsClass.query_region") and
[`query_object`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.query_object "astroquery.mast.ObservationsClass.query_object")), and all observation fields listed
[here](https://mast.stsci.edu/api/v0/_c_a_o_mfields.html).

**Note:** The obstype keyword has been replaced by intentType, with valid values
“calibration” and “science.” If the intentType keyword is not supplied, both science
and calibration observations will be returned.

Argument values are one or more acceptable values for the criterion,
except for fields with a float datatype where the argument should be in the form
[minVal, maxVal]. For non-float type criteria, wildcards (both \* and %) may be used.
However, only one wildcarded value can be processed per criterion.

RA and Dec must be given in decimal degrees, and datetimes in MJD.

[`query_criteria`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.query_criteria "astroquery.mast.ObservationsClass.query_criteria") can be used to perform non-positional criteria queries.

```
>>> from astroquery.mast import Observations
...
>>> obs_table = Observations.query_criteria(dataproduct_type="image",
...                                         proposal_pi="Osten*")
>>> print(obs_table[:5])
intentType obs_collection provenance_name ... srcDen  obsid     objID
---------- -------------- --------------- ... ------ -------- ---------
   science            HST          CALCOS ...    nan 24139596 144540274
   science            HST          CALCOS ...    nan 24139591 144540276
   science            HST          CALCOS ...    nan 24139580 144540277
   science            HST          CALCOS ...    nan 24139597 144540280
   science            HST          CALCOS ...    nan 24139575 144540281
...
```

You can also perform positional queries with additional criteria by passing in `objectname`, `coordinates`,
and/or `radius` as keyword arguments.

```
>>> from astroquery.mast import Observations
...
>>> obs_table = Observations.query_criteria(objectname="M10",
...                                         radius="0.1 deg",
...                                         filters=["*UV","Kepler"],
...                                         obs_collection="GALEX")
>>> print(obs_table)
intentType obs_collection provenance_name ... objID objID1 distance
---------- -------------- --------------- ... ----- ------ --------
   science          GALEX             AIS ... 61675  61675      0.0
   science          GALEX             GII ...  7022   7022      0.0
   science          GALEX             GII ... 78941  78941      0.0
   science          GALEX             AIS ... 61673  61673      0.0
   science          GALEX             GII ...  7023   7023      0.0
   science          GALEX             AIS ... 61676  61676      0.0
   science          GALEX             AIS ... 61674  61674      0.0
```

We encourage the use of wildcards particularly when querying for JWST instruments
with the instrument\_name criteria. This is because of the varying instrument names
for JWST science instruments, which you can read more about on the MAST page for
[JWST Instrument Names](https://outerspace.stsci.edu/display/MASTDOCS/JWST+Instrument+Names).

```
>>> from astroquery.mast import Observations
...
>>> obs_table = Observations.query_criteria(proposal_pi="Espinoza, Nestor",
...                                         instrument_name="NIRISS*")
>>> set(obs_table['instrument_name'])
{'NIRISS', 'NIRISS/IMAGE', 'NIRISS/SOSS'}
```

### Getting Observation Counts

To get the number of observations and not the observations themselves, query\_counts functions are available.
This can be useful if trying to decide whether the available memory is sufficient for the number of observations.

```
>>> from astroquery.mast import Observations
...
>>> print(Observations.query_region_count("322.49324 12.16683", radius=0.001))
6338
...
>>> print(Observations.query_object_count("M8",radius=".02 deg"))
469
...
>>> print(Observations.query_criteria_count(proposal_id=8880))
8
```

## Downloading Data

### Getting Product Lists

Each observation returned from a MAST query can have one or more associated data products.
Given one or more observations or MAST Product Group IDs (“obsid”)
[`get_product_list`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.get_product_list "astroquery.mast.ObservationsClass.get_product_list") will return
a [`Table`](https://docs.astropy.org/en/stable/api/astropy.table.Table.html#astropy.table.Table "(in Astropy v7.1)") containing the associated data products.
The product fields are documented [here](https://mast.stsci.edu/api/v0/_productsfields.html).

```
>>> from astroquery.mast import Observations
...
>>> obs_table = Observations.query_criteria(objectname="M8", obs_collection=["K2", "IUE"])
>>> data_products_by_obs = Observations.get_product_list(obs_table[0:2])
>>> print(data_products_by_obs)
obsID  obs_collection dataproduct_type ... dataRights calib_level filters
------ -------------- ---------------- ... ---------- ----------- -------
664784             K2       timeseries ...     PUBLIC           2  KEPLER
664785             K2       timeseries ...     PUBLIC           2  KEPLER
>>> obsids = obs_table[0:2]['obsid']
>>> data_products_by_id = Observations.get_product_list(obsids)
>>> print(data_products_by_id)
obsID  obs_collection dataproduct_type ... dataRights calib_level filters
------ -------------- ---------------- ... ---------- ----------- -------
664784             K2       timeseries ...     PUBLIC           2  KEPLER
664785             K2       timeseries ...     PUBLIC           2  KEPLER
>>> print((data_products_by_obs == data_products_by_id).all())
True
```

Note that the input to [`get_product_list`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.get_product_list "astroquery.mast.ObservationsClass.get_product_list") should be “obsid” and NOT “obs\_id”,
which is a mission-specific identifier for a given observation, and cannot be used for querying the MAST database
with [`get_product_list`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.get_product_list "astroquery.mast.ObservationsClass.get_product_list")
(see [here](https://mast.stsci.edu/api/v0/_c_a_o_mfields.html) for more details).
Using “obs\_id” instead of “obsid” from the previous example will result in the following error:

```
>>> obs_ids = obs_table[0:2]['obs_id']
>>> data_products_by_id = Observations.get_product_list(obs_ids)
Traceback (most recent call last):
...
RemoteServiceError: Error converting data type varchar to bigint.
```

To return only unique data products for an observation, use [`get_unique_product_list`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.get_unique_product_list "astroquery.mast.ObservationsClass.get_unique_product_list").

```
>>> obs = Observations.query_criteria(obs_collection='HST',
...                                   filters='F606W',
...                                   instrument_name='ACS/WFC',
...                                   proposal_id=['12062'],
...                                   dataRights='PUBLIC')
>>> unique_products = Observations.get_unique_product_list(obs)
INFO: 180 of 370 products were duplicates. Only returning 190 unique product(s). [astroquery.mast.utils]
INFO: To return all products, use `Observations.get_product_list` [astroquery.mast.observations]
>>> print(unique_products[:10]['dataURI'])
                dataURI
----------------------------------------
mast:HST/product/jbeveoesq_flt_hlet.fits
   mast:HST/product/jbeveoesq_spt.fits
   mast:HST/product/jbeveoesq_trl.fits
      mast:HST/product/jbeveoesq_log.txt
      mast:HST/product/jbeveoesq_raw.jpg
      mast:HST/product/jbeveoesq_flc.jpg
      mast:HST/product/jbeveoesq_flt.jpg
   mast:HST/product/jbeveoesq_flc.fits
   mast:HST/product/jbeveoesq_flt.fits
   mast:HST/product/jbeveoesq_raw.fits
```

### Filtering Data Products

In many cases, you will not need to download every product that is associated with a dataset. The
[`filter_products`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.filter_products "astroquery.mast.ObservationsClass.filter_products") function allows for filtering based on minimum recommended products
(`mrp_only`), file extension (`extension`), and any other of the [CAOM products fields](https://mast.stsci.edu/api/v0/_productsfields.html).

The **AND** operation is applied between filters, and the **OR** operation is applied within each filter set, except in the case of negated values.

A filter value can be negated by prefiing it with `!`, meaning that rows matching that value will be excluded from the results.
When any negated value is present in a filter set, any positive values in that set are combined with **OR** logic, and the negated
values are combined with **AND** logic against the positives.

For example:
:   * `productType=['A', 'B', '!C']` → (productType != C) AND (productType == A OR productType == B)
    * `size=['!14400', '<20000']` → (size != 14400) AND (size < 20000)

For columns with numeric data types (`int` or `float`), filter values can be expressed in several ways:
:   * A single number: `size=100`
    * A range in the form “start..end”: `size="100..1000"`
    * A comparison operator followed by a number: `size=">=1000"`
    * A list of expressions: `size=[100, "500..1000", ">=1500"]`

The filter below returns FITS products that have a calibration level of 2 or lower **and** are of type “SCIENCE” **or** “PREVIEW”.

```
>>> from astroquery.mast import Observations
...
>>> data_products = Observations.get_product_list('25588063')
>>> filtered = Observations.filter_products(data_products,
...                                         extension="fits",
...                                         calib_level="<=2",
...                                         productType=["SCIENCE", "PREVIEW"])
>>> print(filtered)
 obsID   obs_collection dataproduct_type ... dataRights calib_level filters
-------- -------------- ---------------- ... ---------- ----------- -------
25167183            HLA            image ...     PUBLIC           2   F487N
24556691            HST            image ...     PUBLIC           2   F487N
24556691            HST            image ...     PUBLIC           2   F487N
24556691            HST            image ...     PUBLIC           2   F487N
24556691            HST            image ...     PUBLIC           2   F487N
24556691            HST            image ...     PUBLIC           1   F487N
24556691            HST            image ...     PUBLIC           1   F487N
24556691            HST            image ...     PUBLIC           2   F487N
```

### Downloading Data Products

The [`download_products`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.download_products "astroquery.mast.ObservationsClass.download_products") function accepts a table of products like the one above
and will download the products to your machine.

By default, products will be downloaded into the current working directory, in a subdirectory called “mastDownload”.
You can change the download directory by passing the `download_dir` keyword argument.

The function also accepts dataset IDs and product filters as input for a more streamlined workflow.

```
>>> from astroquery.mast import Observations
...
>>> single_obs = Observations.query_criteria(obs_collection="IUE", obs_id="lwp13058")
>>> data_products = Observations.get_product_list(single_obs)
...
>>> manifest = Observations.download_products(data_products, productType="SCIENCE")
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=http://archive.stsci.edu/pub/iue/data/lwp/13000/lwp13058.mxlo.gz to ./mastDownload/IUE/lwp13058/lwp13058.mxlo.gz ... [Done]
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=http://archive.stsci.edu/pub/vospectra/iue2/lwp13058mxlo_vo.fits to ./mastDownload/IUE/lwp13058/lwp13058mxlo_vo.fits ... [Done]
...
>>> print(manifest)
                   Local Path                     Status  Message URL
------------------------------------------------ -------- ------- ----
    ./mastDownload/IUE/lwp13058/lwp13058.mxlo.gz COMPLETE    None None
./mastDownload/IUE/lwp13058/lwp13058mxlo_vo.fits COMPLETE    None None
```

​As an alternative to downloading the data files now, the `curl_flag` can be used instead to instead get a
curl script that can be used to download the files at a later time.

```
>>> from astroquery.mast import Observations
...
>>> single_obs = Observations.query_criteria(obs_collection="IUE", obs_id="lwp13058")
>>> data_products = Observations.get_product_list(single_obs)
...
>>> table = Observations.download_products(data_products,
...                                        productType="SCIENCE",
...                                        curl_flag=True)
Downloading URL https://mast.stsci.edu/portal/Download/stage/anonymous/public/514cfaa9-fdc1-4799-b043-4488b811db4f/mastDownload_20170629162916.sh to ./mastDownload_20170629162916.sh ... [Done]
```

### Downloading a Single File

You can download a single data product file by using the [`download_file`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.download_file "astroquery.mast.ObservationsClass.download_file")
method and passing in a MAST Data URI. The default is to download the file to the current working directory, but
you can specify the download directory or filepath with the `local_path` keyword argument.

```
>>> from astroquery.mast import Observations
...
>>> single_obs = Observations.query_criteria(obs_collection="IUE",obs_id="lwp13058")
>>> data_products = Observations.get_product_list(single_obs)
...
>>> product = data_products[0]["dataURI"]
>>> print(product)
mast:IUE/url/pub/iue/data/lwp/13000/lwp13058.elbll.gz
>>> result = Observations.download_file(product)
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:IUE/url/pub/iue/data/lwp/13000/lwp13058.elbll.gz to ./lwp13058.elbll.gz ... [Done]
...
>>> print(result)
('COMPLETE', None, None)
```

The [`download_file`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.download_file "astroquery.mast.ObservationsClass.download_file") and [`download_products`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.download_products "astroquery.mast.ObservationsClass.download_products")
methods are not interchangeable. Using the incorrect method for either single files or product lists will result
in an error.

```
>>> result = Observations.download_products(product)
Traceback (most recent call last):
...
RemoteServiceError: Error converting data type varchar to bigint.
```

```
>>> result = Observations.download_file(data_products)
Traceback (most recent call last):
...
TypeError: can only concatenate str (not "Table") to str
```

### Cloud Data Access

Public datasets from the Hubble, Kepler and TESS telescopes are also available for free on Amazon Web Services
in [public S3 buckets](https://registry.opendata.aws/collab/stsci/).

Using AWS resources to process public data no longer requires an AWS account for all AWS regions.
To enable cloud data access for the Hubble, Kepler, TESS, GALEX, and Pan-STARRS missions, follow the steps below:

You can enable cloud data access via the [`enable_cloud_dataset`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.enable_cloud_dataset "astroquery.mast.ObservationsClass.enable_cloud_dataset")
function, which sets AWS to become the preferred source for data access as opposed to on-premise
MAST until it is disabled with [`disable_cloud_dataset`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.disable_cloud_dataset "astroquery.mast.ObservationsClass.disable_cloud_dataset").

To directly access a list of cloud URIs for a given dataset, use the
[`get_cloud_uris`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.get_cloud_uris "astroquery.mast.ObservationsClass.get_cloud_uris")
function (Python will prompt you to enable cloud access if you haven’t already).
With this function, users may specify a [`Table`](https://docs.astropy.org/en/stable/api/astropy.table.Table.html#astropy.table.Table "(in Astropy v7.1)") of data products or
query criteria. Query criteria are supplied as keyword arguments, and product filters
may be supplied through the `mrp_only`, `extension`, and `filter_products` parameters.

When cloud access is enabled, the standard download function
[`download_products`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.download_products "astroquery.mast.ObservationsClass.download_products") preferentially pulls files from AWS when they
are available. When set to [`True`](https://docs.python.org/3/library/constants.html#True "(in Python v3.13)"), the `cloud_only` parameter in
[`download_products`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.download_products "astroquery.mast.ObservationsClass.download_products") skips all data products not available in the cloud.

To get a list of S3 URIs, use the following workflow:

```
>>> import os
>>> from astroquery.mast import Observations
...
>>> # Simply call the `enable_cloud_dataset` method from `Observations`.
>>> # The default provider is `AWS`, but we will write it in manually for this example:
>>> Observations.enable_cloud_dataset(provider='AWS')
INFO: Using the S3 STScI public dataset [astroquery.mast.core]
...
>>> # Getting the cloud URIs
>>> obs_table = Observations.query_criteria(obs_collection='HST',
...                                         filters='F606W',
...                                         instrument_name='ACS/WFC',
...                                         proposal_id=['12062'],
...                                         dataRights='PUBLIC')
>>> products = Observations.get_product_list(obs_table)
>>> filtered = Observations.filter_products(products,
...                                         productSubGroupDescription='DRZ')
>>> s3_uris = Observations.get_cloud_uris(filtered)
>>> print(s3_uris)
['s3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits', 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits']
...
>>> Observations.disable_cloud_dataset()
```

Alternatively, this workflow can be streamlined by providing the query criteria directly to [`get_cloud_uris`](../api/astroquery.mast.ObservationsClass.html#astroquery.mast.ObservationsClass.get_cloud_uris "astroquery.mast.ObservationsClass.get_cloud_uris").
This approach is recommended for code brevity. Query criteria are supplied as keyword arguments, and filters are supplied through the
`filter_products` parameter. If both `data_products` and query criteria are provided, `data_products` takes precedence.

```
>>> import os
>>> from astroquery.mast import Observations
...
>>> Observations.enable_cloud_dataset(provider='AWS')
INFO: Using the S3 STScI public dataset [astroquery.mast.cloud]
>>> # Getting the cloud URIs
>>> s3_uris = Observations.get_cloud_uris(obs_collection='HST',
...                                       filters='F606W',
...                                       instrument_name='ACS/WFC',
...                                       proposal_id=['12062'],
...                                       dataRights='PUBLIC',
...                                       filter_products={'productSubGroupDescription': 'DRZ'})
INFO: 2 of 4 products were duplicates. Only returning 2 unique product(s). [astroquery.mast.utils]
>>> print(s3_uris)
['s3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits', 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits']
>>> Observations.disable_cloud_dataset()
```

Downloading data products from S3:

```
>>> import os
>>> from astroquery.mast import Observations
...
>>> # Simply call the `enable_cloud_dataset` method from `Observations`. The default provider is `AWS`, but we will write it in manually for this example:
>>> Observations.enable_cloud_dataset(provider='AWS')
INFO: Using the S3 STScI public dataset [astroquery.mast.core]
...
>>> # Downloading from the cloud
>>> obs_table = Observations.query_criteria(obs_collection=['Kepler'],
...                                         objectname="Kepler 12b", radius=0)
>>> products = Observations.get_product_list(obs_table[0])
>>> manifest = Observations.download_products(products[:10], cloud_only=True)
manifestDownloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465-01-20160209194854_dvs.pdf to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-01-20160209194854_dvs.pdf ...
|==========================================| 1.5M/1.5M (100.00%)         0s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465-20160128150956_dvt.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-20160128150956_dvt.fits ...
|==========================================|  17M/ 17M (100.00%)         1s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465-20160209194854_dvr.pdf to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-20160209194854_dvr.pdf ...
|==========================================| 5.8M/5.8M (100.00%)         0s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465_q1_q17_dr25_obs_tcert.pdf to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465_q1_q17_dr25_obs_tcert.pdf ...
|==========================================| 2.2M/2.2M (100.00%)         0s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/previews/0118/011804465/kplr011804465-2013011073258_llc_bw_large.png to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2013011073258_llc_bw_large.png ...
|==========================================|  24k/ 24k (100.00%)         0s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/target_pixel_files/0118/011804465/kplr011804465_tpf_lc_Q111111110111011101.tar to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465_tpf_lc_Q111111110111011101.tar ...
|==========================================|  43M/ 43M (100.00%)         4s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465_lc_Q111111110111011101.tar to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465_lc_Q111111110111011101.tar ...
|==========================================| 5.9M/5.9M (100.00%)         0s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465-2009131105131_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009131105131_llc.fits ...
|==========================================|  77k/ 77k (100.00%)         0s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465-2009166043257_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009166043257_llc.fits ...
|==========================================| 192k/192k (100.00%)         0s
Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465-2009259160929_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009259160929_llc.fits ...
|==========================================| 466k/466k (100.00%)         0s
...
>>> print(manifest["Status"])
Status
--------
COMPLETE
COMPLETE
COMPLETE
COMPLETE
COMPLETE
COMPLETE
COMPLETE
COMPLETE
COMPLETE
COMPLETE
...
>>> Observations.disable_cloud_dataset()
```