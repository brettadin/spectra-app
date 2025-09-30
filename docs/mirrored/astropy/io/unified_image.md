# Image Data

Reading and writing CCD image data in the unified I/O interface is supported
though the [CCDData class](../nddata/ccddata.html#ccddata) using FITS file format:

```
>>> # Read CCD image
>>> from astropy.nddata import CCDData
>>> ccd = CCDData.read('image.fits')

>>> # Write back CCD image
>>> ccd.write('new_image.fits')
```

Note that the unit is stored in the `BUNIT` keyword in the header on saving,
and is read from the header if it is present.

Detailed help on the available keyword arguments for reading and writing
can be obtained via the `help()` method as follows:

```
>>> from astropy.nddata import CCDData
>>> CCDData.read.help('fits')  # Get help on the CCDData FITS reader
=========================================
CCDData.read(format='fits') documentation
=========================================
...
>>> CCDData.write.help('fits')  # Get help on the CCDData FITS writer
==========================================
CCDData.write(format='fits') documentation
==========================================
...
```