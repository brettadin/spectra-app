### Examples

To create a [`Time`](../api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time") object:

```
>>> import numpy as np
>>> from astropy.time import Time
>>> times = ['1999-01-01T00:00:00.123456789', '2010-01-01T00:00:00']
>>> t = Time(times, format='isot', scale='utc')
>>> t
<Time object: scale='utc' format='isot' value=['1999-01-01T00:00:00.123' '2010-01-01T00:00:00.000']>
>>> t[1]
<Time object: scale='utc' format='isot' value=2010-01-01T00:00:00.000>
```

The `format` argument specifies how to interpret the input values (e.g., ISO,
JD, or Unix time). By default, the same format will be used to represent the
time for output. One can change this format later as needed, but because this
is just for representation, that does not affect the internal representation
(which is always by two 64-bit values, the `jd1` and `jd2` attributes), nor
any computations with the object.

The `scale` argument specifies the [time scale](#id6) for the values
(e.g., UTC, TT, or UT1). The `scale` argument is optional and defaults
to UTC except for [Time from Epoch Formats](#time-from-epoch-formats). It is possible to change
it (e.g., from UTC to TDB), which will cause the internal values to be
adjusted accordingly.

We could have written the above as:

```
>>> t = Time(times, format='isot')
```

When the format of the input can be unambiguously determined, the
`format` argument is not required, so we can then simplify even further:

Now we can get the representation of these times in the JD and MJD
formats by requesting the corresponding [`Time`](../api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time") attributes:

```
>>> t.jd
array([2451179.50000143, 2455197.5       ])
>>> t.mjd
array([51179.00000143, 55197.        ])
```

The full power of output representation is available via the
[`to_value`](../api/astropy.time.Time.html#astropy.time.Time.to_value "astropy.time.Time.to_value") method which also allows controlling the
[subformat](#subformat). For instance, using `numpy.longdouble` as the output type
for higher precision:

```
>>> t.to_value('mjd', 'long')
array([51179.00000143, 55197.        ], dtype=float128)
```

The default representation can be changed by setting the `format` attribute:

```
>>> t.format = 'fits'
>>> t
<Time object: scale='utc' format='fits' value=['1999-01-01T00:00:00.123'
                                               '2010-01-01T00:00:00.000']>
>>> t.format = 'isot'
```

We can also convert to a different time scale, for instance from UTC to
TT. This uses the same attribute mechanism as above but now returns a new
[`Time`](../api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time") object:

```
>>> t2 = t.tt
>>> t2
<Time object: scale='tt' format='isot' value=['1999-01-01T00:01:04.307' '2010-01-01T00:01:06.184']>
>>> t2.jd
array([2451179.5007443 , 2455197.50076602])
```

Note that both the ISO (ISOT) and JD representations of `t2` are different
than for `t` because they are expressed relative to the TT time scale. Of
course, from the numbers or strings you would not be able to tell this was the
case:

```
>>> print(t2.fits)
['1999-01-01T00:01:04.307' '2010-01-01T00:01:06.184']
```

You can set the time values in place using the usual `numpy` array setting
item syntax:

```
>>> t2 = t.tt.copy()  # Copy required if transformed Time will be modified
>>> t2[1] = '2014-12-25'
>>> print(t2)
['1999-01-01T00:01:04.307' '2014-12-25T00:00:00.000']
```

The [`Time`](../api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time") object also has support for missing values, which is particularly
useful for [Table Operations](../table/operations.html#table-operations) such as joining and stacking:

```
>>> t2[0] = np.ma.masked  # Declare that first time is missing or invalid
>>> print(t2)
[                      ——— '2014-12-25T00:00:00.000']
```

Finally, some further examples of what is possible. For details, see
the API documentation below.

```
>>> dt = t[1] - t[0]
>>> dt
<TimeDelta object: scale='tai' format='jd' value=4018.00002172>
```

Here, note the conversion of the timescale to TAI. Time differences
can only have scales in which one day is always equal to 86400 seconds.

```
>>> import numpy as np
>>> t[0] + dt * np.linspace(0., 1., 12)
<Time object: scale='utc' format='isot' value=['1999-01-01T00:00:00.123' '2000-01-01T06:32:43.930'
 '2000-12-31T13:05:27.737' '2001-12-31T19:38:11.544'
 '2003-01-01T02:10:55.351' '2004-01-01T08:43:39.158'
 '2004-12-31T15:16:22.965' '2005-12-31T21:49:06.772'
 '2007-01-01T04:21:49.579' '2008-01-01T10:54:33.386'
 '2008-12-31T17:27:17.193' '2010-01-01T00:00:00.000']>
```

```
>>> t.sidereal_time('apparent', 'greenwich')
<Longitude [6.68050179, 6.70281947] hourangle>
```

You can also use time-based [`Quantity`](../api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity") for time arithmetic:

```
>>> import astropy.units as u
>>> Time("2020-01-01") + 5 * u.day
<Time object: scale='utc' format='iso' value=2020-01-06 00:00:00.000>
```

As of v5.1, [`Time`](../api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time") objects can also be passed directly to
[`numpy.linspace`](https://numpy.org/doc/stable/reference/generated/numpy.linspace.html#numpy.linspace "(in NumPy v2.3)") to create even-sampled time arrays, including support for
non-scalar `start` and/or `stop` points - given compatible shapes.

```
>>> stop = ['1999-01-05T00:00:00.123456789', '2010-05-01T00:00:00']
>>> tstp = Time(stop, format='isot', scale='utc')
>>> np.linspace(t, tstp, 4, endpoint=False)
<Time object: scale='utc' format='isot' value=[['1999-01-01T00:00:00.123' '2010-01-01T00:00:00.000']
 ['1999-01-02T00:00:00.123' '2010-01-31T00:00:00.000']
 ['1999-01-03T00:00:00.123' '2010-03-02T00:00:00.000']
 ['1999-01-04T00:00:00.123' '2010-04-01T00:00:00.000']]>
```