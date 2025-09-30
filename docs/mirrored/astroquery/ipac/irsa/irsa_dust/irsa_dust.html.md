### Fetch images

Retrieve the image cut-outs for the specified object name or coordinates. The
images fetched in the FITS format and the result is returned as a list of
[`HDUList`](https://docs.astropy.org/en/stable/io/fits/api/hdulists.html#astropy.io.fits.HDUList "(in Astropy v7.1)") objects. For all image queries, the radius may be optionally
specified. If missing the radius defaults to 5 degrees. Note that radius may be
specified in any appropriate unit, however it must fall in the range of 2 to
37.5 degrees.

```
>>> from astroquery.ipac.irsa.irsa_dust import IrsaDust
>>> image_list = IrsaDust.get_images("m81")
Downloading http://irsa.ipac.caltech.edu//workspace/TMP_pdTImE_1525/DUST/m81.v0001/p414Dust.fits
|===========================================| 331k/331k (100.00%)        15s
Downloading http://irsa.ipac.caltech.edu//workspace/TMP_pdTImE_1525/DUST/m81.v0001/p414i100.fits
|===========================================| 331k/331k (100.00%)        13s
Downloading http://irsa.ipac.caltech.edu//workspace/TMP_pdTImE_1525/DUST/m81.v0001/p414temp.fits
|===========================================| 331k/331k (100.00%)        05s
>>> image_list
[[<astropy.io.fits.hdu.image.PrimaryHDU at 0x39b8610>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x39b8bd0>],
[<astropy.io.fits.hdu.image.PrimaryHDU at 0x39bd8d0>]]
```

Image queries return cutouts for 3 images - E(B-V) reddening, 100 micron
intensity, and dust temperature maps. If only the image of a particular type is
required, then this may be specified by using the `image_type` keyword argument
to the [`get_images()`](../../../api/astroquery.ipac.irsa.irsa_dust.IrsaDustClass.html#astroquery.ipac.irsa.irsa_dust.IrsaDustClass.get_images "astroquery.ipac.irsa.irsa_dust.IrsaDustClass.get_images") method. It can take on one of the three values
`ebv`, `100um` and `temperature`, corresponding to each of the 3 kinds of
images:

```
>>> from astroquery.ipac.irsa.irsa_dust import IrsaDust
>>> import astropy.units as u
>>> image = IrsaDust.get_images("m81", image_type="100um", radius=2*u.deg)
Downloading http://irsa.ipac.caltech.edu//workspace/TMP_007Vob_24557/DUST/m81.v0001/p414i100.fits
|===========================================| 149k/149k (100.00%)        02s
>>> image
[[<astropy.io.fits.hdu.image.PrimaryHDU at 0x3a5a650>]]
```

The image types that are available can also be listed out any time:

```
>>> from astroquery.ipac.irsa.irsa_dust import IrsaDust
>>> IrsaDust.list_image_types()
['temperature', 'ebv', '100um']
```

The target may also be specified via coordinates passed as strings. Examples of acceptable coordinate
strings can be found on this [IRSA DUST coordinates description page](https://irsa.ipac.caltech.edu:443/applications/DUST/docs/coordinate.html).

```
>>> from astroquery.ipac.irsa.irsa_dust import IrsaDust
>>> import astropy.coordinates as coord
>>> import astropy.units as u
>>> image_list = IrsaDust.get_images("17h44m34s -27d59m13s", radius=2.0 * u.deg)
Downloading http://irsa.ipac.caltech.edu//workspace/TMP_46IWzq_9460/DUST/17h44m34s_-27d59m13s.v0001/p118Dust.fits
|==============================|  57k/ 57k (100.00%)        00s
Downloading http://irsa.ipac.caltech.edu//workspace/TMP_46IWzq_9460/DUST/17h44m34s_-27d59m13s.v0001/p118i100.fits
|==============================|  57k/ 57k (100.00%)        00s
Downloading http://irsa.ipac.caltech.edu//workspace/TMP_46IWzq_9460/DUST/17h44m34s_-27d59m13s.v0001/p118temp.fits
|==============================|  57k/ 57k (100.00%)        00s
```

A list having the download links for the FITS image may also be fetched, rather
than the actual images, via the [`get_image_list()`](../../../api/astroquery.ipac.irsa.irsa_dust.IrsaDustClass.html#astroquery.ipac.irsa.irsa_dust.IrsaDustClass.get_image_list "astroquery.ipac.irsa.irsa_dust.IrsaDustClass.get_image_list") method. This also
supports the `image_type` argument, in the same way as described for
[`get_images()`](../../../api/astroquery.ipac.irsa.irsa_dust.IrsaDustClass.html#astroquery.ipac.irsa.irsa_dust.IrsaDustClass.get_images "astroquery.ipac.irsa.irsa_dust.IrsaDustClass.get_images").

```
>>> from astroquery.ipac.irsa.irsa_dust import IrsaDust
>>> import astropy.coordinates as coord
>>> import astropy.units as u
>>> coo = coord.SkyCoord(34.5565*u.deg, 54.2321*u.deg, frame='galactic')
>>> image_urls = IrsaDust.get_image_list(coo)
>>> image_urls
['http://irsa.ipac.caltech.edu//workspace/TMP_gB3awn_6492/DUST/34.5565_54.2321_gal.v0001/p292Dust.fits',
'http://irsa.ipac.caltech.edu//workspace/TMP_gB3awn_6492/DUST/34.5565_54.2321_gal.v0001/p292i100.fits',
'http://irsa.ipac.caltech.edu//workspace/TMP_gB3awn_6492/DUST/34.5565_54.2321_gal.v0001/p292temp.fits']
```