## Introduction

World Coordinate Systems (WCSs) describe the geometric transformations
between one set of coordinates and another. A common application is to
map the pixels in an image onto the celestial sphere. Another common
application is to map pixels to wavelength in a spectrum.

[`astropy.wcs`](reference_api.html#module-astropy.wcs "astropy.wcs") contains utilities for managing World Coordinate System
(WCS) transformations defined in several elaborate [FITS WCS standard](https://fits.gsfc.nasa.gov/fits_wcs.html) conventions.
These transformations work both forward (from pixel to world) and backward
(from world to pixel).

For historical reasons and to support legacy software, [`astropy.wcs`](reference_api.html#module-astropy.wcs "astropy.wcs") maintains
two separate application interfaces. The `High-Level API` should be used by
most applications. It abstracts out the underlying object and works transparently
with other packages which support the
[Common Python Interface for WCS](https://zenodo.org/record/1188875#.XnpOtJNKjyI),
allowing for a more flexible approach to the problem and avoiding the [limitations
of the FITS WCS standard](https://ui.adsabs.harvard.edu/abs/2015A%26C....12..133T/abstract).

The `Low Level API` is the original [`astropy.wcs`](reference_api.html#module-astropy.wcs "astropy.wcs") API and originally developed as `pywcs`.
It ties applications to the [`astropy.wcs`](reference_api.html#module-astropy.wcs "astropy.wcs") package and limits the transformations to the three distinct
types supported by it:

### Pixel Conventions and Definitions

Both APIs assume that integer pixel values fall at the center of pixels (as assumed in
the [FITS WCS standard](https://fits.gsfc.nasa.gov/fits_wcs.html), see Section 2.1.4 of [Greisen et al., 2002,
A&A 446, 747](https://doi.org/10.1051/0004-6361:20053818)).

However, there’s a difference in what is considered to be the first pixel. The
`High Level API` follows the Python and C convention that the first pixel is
the 0-th one, i.e. the first pixel spans pixel values -0.5 to + 0.5. The
`Low Level API` takes an additional `origin` argument with values of 0 or 1
indicating whether the input arrays are 0- or 1-based.
The Low-level interface assumes Cartesian order (x, y) of the input coordinates,
however the Common Interface for World Coordinate System accepts both conventions.
The order of the pixel coordinates ((x, y) vs (row, column)) in the Common API
depends on the method or property used, and this can normally be determined from
the property or method name. Properties and methods containing “pixel” assume (x, y)
ordering, while properties and methods containing “array” assume (row, column) ordering.