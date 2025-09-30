```
>>> from astroquery.hips2fits import hips2fits
>>> import matplotlib.pyplot as plt
>>> from matplotlib.colors import Colormap
>>> from astropy import wcs as astropy_wcs
>>> # Create a new WCS astropy object
>>> w = astropy_wcs.WCS(header={
...     'NAXIS1': 2000,         # Width of the output fits/image
...     'NAXIS2': 1000,         # Height of the output fits/image
...     'WCSAXES': 2,           # Number of coordinate axes
...     'CRPIX1': 1000.0,       # Pixel coordinate of reference point
...     'CRPIX2': 500.0,        # Pixel coordinate of reference point
...     'CDELT1': -0.18,        # [deg] Coordinate increment at reference point
...     'CDELT2': 0.18,         # [deg] Coordinate increment at reference point
...     'CUNIT1': 'deg',        # Units of coordinate increment and value
...     'CUNIT2': 'deg',        # Units of coordinate increment and value
...     'CTYPE1': 'GLON-MOL',   # galactic longitude, Mollweide's projection
...     'CTYPE2': 'GLAT-MOL',   # galactic latitude, Mollweide's projection
...     'CRVAL1': 0.0,          # [deg] Coordinate value at reference point
...     'CRVAL2': 0.0,          # [deg] Coordinate value at reference point
... })
>>> hips = 'CDS/P/DSS2/red'
>>> result = hips2fits.query_with_wcs(
...    hips=hips,
...    wcs=w,
...    get_query_payload=False,
...    format='jpg',
...    min_cut=0.5,
...    max_cut=99.5,
...    cmap=Colormap('viridis'),
... )
>>> im = plt.imshow(result)
>>> plt.show()
```