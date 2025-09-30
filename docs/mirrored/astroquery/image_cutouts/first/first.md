```
>>> from astroquery.image_cutouts.first import First
>>> from astropy import coordinates
>>> from astropy import units as u
>>> image = First.get_images(coordinates.SkyCoord(162.530*u.deg, 30.677*u.deg,
...                                                frame='icrs'))
>>> image

[<astropy.io.fits.hdu.image.PrimaryHDU object at 0x11c189390>]
```