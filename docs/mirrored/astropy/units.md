### Examples

To create a [`Quantity`](../api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity") object:

```
>>> from astropy import units as u
>>> 42.0 * u.meter
<Quantity  42. m>
>>> [1., 2., 3.] * u.m
<Quantity [1., 2., 3.] m>
>>> import numpy as np
>>> np.array([1., 2., 3.]) * u.m
<Quantity [1., 2., 3.] m>
```

You can get the unit and value from a [`Quantity`](../api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity") using the unit and
value members:

```
>>> q = 42.0 * u.meter
>>> q.value
np.float64(42.0)
>>> q.unit
Unit("m")
```

From this basic building block, it is possible to start combining
quantities with different units:

```
>>> 15.1 * u.meter / (32.0 * u.second)
<Quantity 0.471875 m / s>
>>> 3.0 * u.kilometer / (130.51 * u.meter / u.second)
<Quantity 0.022986744310780783 km s / m>
>>> (3.0 * u.kilometer / (130.51 * u.meter / u.second)).decompose()
<Quantity 22.986744310780782 s>
```

Unit conversion is done using the
[`to()`](../api/astropy.units.Quantity.html#astropy.units.Quantity.to "astropy.units.quantity.Quantity") method, which returns a new
[`Quantity`](../api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity") in the given unit:

```
>>> x = 1.0 * u.parsec
>>> x.to(u.km)
<Quantity 30856775814671.914 km>
```

It is also possible to work directly with units at a lower level, for
example, to create custom units:

```
>>> from astropy.units import imperial

>>> cms = u.cm / u.s
>>> # ...and then use some imperial units
>>> mph = imperial.mile / u.hour

>>> # And do some conversions
>>> q = 42.0 * cms
>>> q.to(mph)
<Quantity 0.939513242662849 mi / h>
```

Units that “cancel out” become a special unit called the
“dimensionless unit”:

```
>>> u.m / u.m
Unit(dimensionless)
```

To create a basic [dimensionless quantity](standard_units.html#doc-dimensionless-unit),
multiply a value by the unscaled dimensionless unit:

```
>>> q = 1.0 * u.dimensionless_unscaled
>>> q.unit
Unit(dimensionless)
```

[`astropy.units`](ref_api.html#module-astropy.units "astropy.units") is able to match compound units against the units it already
knows about:

```
>>> (u.s ** -1).compose()
[Unit("Bq"), Unit("Hz"), Unit("2.7027e-11 Ci")]
```

And it can convert between unit systems, such as [SI](https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf) or [CGS](https://en.wikipedia.org/wiki/Centimetre-gram-second_system_of_units):

```
>>> (1.0 * u.Pa).cgs
<Quantity 10. Ba>
```

The units `mag`, `dex`, and `dB` are special, being [logarithmic
units](logarithmic_units.html#logarithmic-units), for which a value is the logarithm of a physical
quantity in a given unit. These can be used with a physical unit in
parentheses to create a corresponding logarithmic quantity:

```
>>> -2.5 * u.mag(u.ct / u.s)
<Magnitude -2.5 mag(ct / s)>
>>> from astropy import constants as c
>>> u.Dex((c.G * u.M_sun / u.R_sun**2).cgs)
<Dex 4.438067627303133 dex(cm / s2)>
```

[`astropy.units`](ref_api.html#module-astropy.units "astropy.units") also handles [equivalencies](equivalencies.html#unit-equivalencies), such as
that between wavelength and frequency. To use that feature, equivalence objects
are passed to the [`to()`](../api/astropy.units.Quantity.html#astropy.units.Quantity.to "astropy.units.quantity.Quantity") conversion
method. For instance, a conversion from wavelength to frequency does not
normally work:

```
>>> (1000 * u.nm).to(u.Hz)
Traceback (most recent call last):
  ...
UnitConversionError: 'nm' (length) and 'Hz' (frequency) are not convertible
```

But by passing an equivalency list, in this case
[`spectral()`](../api/astropy.units.spectral.html#astropy.units.spectral "astropy.units.spectral"), it does:

```
>>> (1000 * u.nm).to(u.Hz, equivalencies=u.spectral())
<Quantity  2.99792458e+14 Hz>
```

Quantities and units can be [printed nicely to strings](format.html#astropy-units-format) using the [Format String Syntax](https://docs.python.org/3/library/string.html#format-string-syntax). Format
specifiers (like `0.03f`) in strings will be used to format the quantity
value:

```
>>> q = 15.1 * u.meter / (32.0 * u.second)
>>> q
<Quantity 0.471875 m / s>
>>> f"{q:0.03f}"
'0.472 m / s'
```

The value and unit can also be formatted separately. Format specifiers
for units can be used to choose the unit formatter:

```
>>> q = 15.1 * u.meter / (32.0 * u.second)
>>> q
<Quantity 0.471875 m / s>
>>> f"{q.value:0.03f} {q.unit:FITS}"
'0.472 m s-1'
```