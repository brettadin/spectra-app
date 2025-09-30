#### Simple image access queries

[`query_sia`](../../api/astroquery.ipac.irsa.IrsaClass.html#astroquery.ipac.irsa.IrsaClass.query_sia "astroquery.ipac.irsa.IrsaClass.query_sia") provides a way to access IRSA’s Simple
Image Access VO service. In the following example we are looking for Spitzer
Enhanced Imaging products in the centre of the COSMOS field as a [`Table`](https://docs.astropy.org/en/stable/api/astropy.table.Table.html#astropy.table.Table "(in Astropy v7.1)").

Note

There are two versions of SIA queries. This IRSA module in astroquery supports the newer,
version 2. However not all IRSA image collections have been migrated into
the newer protocol yet. If you want access to these, please use
[PyVO](https://pyvo.readthedocs.io/en/latest/) directly as showcased in the
[IRSA tutorials](https://caltech-ipac.github.io/irsa-tutorials/#accessing-irsa-s-on-premises-holdings-using-vo-protocols).

For more info, visit the [IRSA documentation](https://irsa.ipac.caltech.edu/ibe/sia_v1.html).

```
>>> from astroquery.ipac.irsa import Irsa
>>> from astropy.coordinates import SkyCoord
>>> from astropy import units as u
>>>
>>> coord = SkyCoord('150.01d 2.2d', frame='icrs')
>>> spitzer_images = Irsa.query_sia(pos=(coord, 1 * u.arcmin), collection='spitzer_seip')
```

The collection name, `spitzer_seip` in this example,
can be obtained from the collection-query API detailed below.

The result, in this case in `spitzer_images`, is a table of image metadata in the IVOA “ObsCore” format
(see the [ObsCore v1.1 documentation](https://www.ivoa.net/documents/ObsCore/20170509/index.html)).

Now you can open the FITS image and, if desired, make a cutout from
one of the science images.
You could either use
the the IRSA on-premises data or the cloud version of it using the
`access_url` or `cloud_access` columns. For more info about fits
cutouts, please visit [Obtaining subsets from cloud-hosted FITS files](https://docs.astropy.org/en/stable/io/fits/usage/cloud.html#fits-io-cloud "(in Astropy v7.1)").

```
>>> from astropy.io import fits
>>> from astropy.nddata import Cutout2D
>>> from astropy.wcs import WCS
>>> science_image = spitzer_images[spitzer_images['dataproduct_subtype'] == 'science'][0]
>>> with fits.open(science_image['access_url'], use_fsspec=True) as hdul:
...     cutout = Cutout2D(hdul[0].section, position=coord, size=2 * u.arcmin, wcs=WCS(hdul[0].header))
```

Now you can plot the cutout.

```
>>> import matplotlib.pyplot as plt
>>> plt.imshow(cutout.data, cmap='grey')
>>> plt.show()
```

([`Source code`](../../_downloads/2de1e04055297298977bb40a21af88f2/irsa-1.py), [`png`](../../_downloads/2da185723b23314cf8f8274ff8d997d8/irsa-1.png), [`hires.png`](../../_downloads/c925e7b891ab9e78a3db4dbcc1ce4bff/irsa-1.hires.png), [`pdf`](../../_downloads/0d391e10539c906fbbc4d486208d94ed/irsa-1.pdf))

![../../_images/irsa-1.png](../../_images/irsa-1.png)

#### Collection queries

To list available collections for SIA queries, the
[`list_collections`](../../api/astroquery.ipac.irsa.IrsaClass.html#astroquery.ipac.irsa.IrsaClass.list_collections "astroquery.ipac.irsa.IrsaClass.list_collections") method is provided, and
will return a [`Table`](https://docs.astropy.org/en/stable/api/astropy.table.Table.html#astropy.table.Table "(in Astropy v7.1)").
You can use the `filter` argument to show
only collections with a given search string in the collection names.
The `servicetype` argument is used to filter for image collections, using `'SIA'`,
or spectral collections (also see below), using `'SSA'`.

Note

The query underneath `list_collections` is cached on the server
side, and therefore should return quickly with results.
If you experience query timeout, please open an IRSA helpdesk ticket.

```
>>> from astroquery.ipac.irsa import Irsa
>>> Irsa.list_collections(servicetype='SIA', filter='spitzer')
<Table length=38>
     collection
       object
-------------------
  spitzer_abell1763
      spitzer_clash
spitzer_cosmic_dawn
       spitzer_cygx
  spitzer_deepdrill
                ...
      spitzer_spuds
    spitzer_srelics
       spitzer_ssdf
      spitzer_swire
     spitzer_taurus
```