## Getting Started

A number of different tools are contained in the stats package, and
they can be accessed by importing them:

```
>>> from astropy import stats
```

A full list of the different tools are provided below. Please see the
documentation for their different usages. For example, sigma clipping,
which is a common way to estimate the background of an image, can be
performed with the [`sigma_clip()`](../api/astropy.stats.sigma_clip.html#astropy.stats.sigma_clip "astropy.stats.sigma_clip") function.
By default, the function returns a masked array, a type of Numpy array
used for handling missing or invalid entries. Masked arrays retain the
original data but also store another boolean array of the same shape
where `True` indicates that the value is masked. Most Numpy ufuncs
will understand masked arrays and treat them appropriately.
For example, consider the following dataset with a clear outlier:

```
>>> import numpy as np
>>> from astropy.stats import sigma_clip
>>> x = np.array([1, 0, 0, 1, 99, 0, 0, 1, 0])
```

The mean is skewed by the outlier:

```
>>> x.mean()
np.float64(11.333333333333334)
```

Sigma-clipping (3 sigma by default) returns a masked array,
and so functions like `mean` will ignore the outlier:

```
>>> clipped = sigma_clip(x)
>>> clipped
masked_array(data=[1, 0, 0, 1, --, 0, 0, 1, 0],
             mask=[False, False, False, False,  True, False, False, False,
                   False],
       fill_value=999999)
>>> clipped.mean()
np.float64(0.375)
```

If you need to access the original data directly, you can use the
`data` property. Combined with the `mask` property, you can get the
original outliers, or the values that were not clipped:

```
>>> outliers = clipped.data[clipped.mask]
>>> outliers
array([99])
>>> valid = clipped.data[~clipped.mask]
>>> valid
array([1, 0, 0, 1, 0, 0, 1, 0])
```

For more information on masked arrays, including see the
[numpy.ma module](https://numpy.org/doc/stable/reference/maskedarray.generic.html#maskedarray-generic "(in NumPy v2.3)").

### Examples

To estimate the background of an image:

```
>>> data = [1, 5, 6, 8, 100, 5, 3, 2]
>>> data_clipped = stats.sigma_clip(data, sigma=2, maxiters=5)
>>> data_clipped
masked_array(data=[1, 5, 6, 8, --, 5, 3, 2],
             mask=[False, False, False, False,  True, False, False, False],
       fill_value=999999)
>>> np.mean(data_clipped)
np.float64(4.285714285714286)
```

Alternatively, the [`SigmaClip`](../api/astropy.stats.SigmaClip.html#astropy.stats.SigmaClip "astropy.stats.SigmaClip") class provides an
object-oriented interface to sigma clipping, which also returns a
masked array by default:

```
>>> sigclip = stats.SigmaClip(sigma=2, maxiters=5)
>>> sigclip(data)
masked_array(data=[1, 5, 6, 8, --, 5, 3, 2],
             mask=[False, False, False, False,  True, False, False, False],
       fill_value=999999)
```

In addition, there are also several convenience functions for making
the calculation of statistics even more convenient. For example,
[`sigma_clipped_stats()`](../api/astropy.stats.sigma_clipped_stats.html#astropy.stats.sigma_clipped_stats "astropy.stats.sigma_clipped_stats") will return the mean,
median, and standard deviation of a sigma-clipped array:

```
>>> stats.sigma_clipped_stats(data, sigma=2, maxiters=5)
(np.float64(4.285714285714286), np.float64(5.0), np.float64(2.249716535431946))
```

There are also tools for calculating [robust statistics](robust.html#stats-robust), sampling the data, [circular statistics](circ.html#stats-circular), confidence limits, spatial statistics, and adaptive
histograms.

Most tools are fairly self-contained, and include relevant examples in
their docstrings.

## Performance Tips

If you are finding sigma clipping to be slow, and if you have not already done
so, consider installing the [bottleneck](https://pypi.org/project/Bottleneck/)
package, which will speed up some of the internal computations. In addition, if
you are using standard functions for `cenfunc` and/or `stdfunc`, make sure
you specify these as strings rather than passing a NumPy function — that is,
use:

```
>>> sigma_clip(array, cenfunc='median')
```

instead of:

```
>>> sigma_clip(array, cenfunc=np.nanmedian)
```

Using strings will allow the sigma-clipping algorithm to pick the fastest
implementation available for finding the median.