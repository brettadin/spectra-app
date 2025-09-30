# Python warnings system

Astropy uses the Python [`warnings`](https://docs.python.org/3/library/warnings.html#module-warnings "(in Python v3.13)") module to issue warning messages. The
details of using the warnings module are general to Python, and apply to any
Python software that uses this system. The user can suppress the warnings
using the python command line argument `-W"ignore"` when starting an
interactive python session. For example:

The user may also use the command line argument when running a python script as
follows:

```
$ python -W"ignore" myscript.py
```

It is also possible to suppress warnings from within a python script. For
instance, the warnings issued from a single call to the
[`astropy.io.fits.writeto`](io/fits/api/files.html#astropy.io.fits.writeto "astropy.io.fits.writeto") function may be suppressed from within a Python
script using the [`warnings.filterwarnings`](https://docs.python.org/3/library/warnings.html#warnings.filterwarnings "(in Python v3.13)") function as follows:

```
>>> import warnings
>>> from astropy.io import fits
>>> warnings.filterwarnings('ignore', category=UserWarning, append=True)
>>> fits.writeto(filename, data, overwrite=True)
```

An equivalent way to insert an entry into the list of warning filter specifications
for simple call [`warnings.simplefilter`](https://docs.python.org/3/library/warnings.html#warnings.simplefilter "(in Python v3.13)"):

```
>>> warnings.simplefilter('ignore', UserWarning)
```

Astropy includes its own warning classes,
[`AstropyWarning`](api/astropy.utils.exceptions.AstropyWarning.html#astropy.utils.exceptions.AstropyWarning "astropy.utils.exceptions.AstropyWarning") and
[`AstropyUserWarning`](api/astropy.utils.exceptions.AstropyUserWarning.html#astropy.utils.exceptions.AstropyUserWarning "astropy.utils.exceptions.AstropyUserWarning"). All warnings from Astropy are
based on these warning classes (see below for the distinction between them). One
can thus ignore all warnings from Astropy (while still allowing through
warnings from other libraries like Numpy) by using something like:

```
>>> from astropy.utils.exceptions import AstropyWarning
>>> warnings.simplefilter('ignore', category=AstropyWarning)
```

Warning filters may also be modified just within a certain context using the
[`warnings.catch_warnings`](https://docs.python.org/3/library/warnings.html#warnings.catch_warnings "(in Python v3.13)") context manager:

```
>>> with warnings.catch_warnings():
...     warnings.simplefilter('ignore', AstropyWarning)
...     fits.writeto(filename, data, overwrite=True)
```

As mentioned above, there are actually *two* base classes for Astropy warnings.
The main distinction is that [`AstropyUserWarning`](api/astropy.utils.exceptions.AstropyUserWarning.html#astropy.utils.exceptions.AstropyUserWarning "astropy.utils.exceptions.AstropyUserWarning") is
for warnings that are *intended* for typical users (e.g. “Warning: Ambiguous
unit”, something that might be because of improper input). In contrast,
[`AstropyWarning`](api/astropy.utils.exceptions.AstropyWarning.html#astropy.utils.exceptions.AstropyWarning "astropy.utils.exceptions.AstropyWarning") warnings that are *not*
[`AstropyUserWarning`](api/astropy.utils.exceptions.AstropyUserWarning.html#astropy.utils.exceptions.AstropyUserWarning "astropy.utils.exceptions.AstropyUserWarning") may be for lower-level warnings
more useful for developers writing code that *uses* Astropy (e.g., the
deprecation warnings discussed below). So if you’re a user that just wants to
silence everything, the code above will suffice, but if you are a developer and
want to hide development-related warnings from your users, you may wish to still
allow through [`AstropyUserWarning`](api/astropy.utils.exceptions.AstropyUserWarning.html#astropy.utils.exceptions.AstropyUserWarning "astropy.utils.exceptions.AstropyUserWarning").

Astropy also issues warnings when deprecated API features are used. If you
wish to *squelch* deprecation warnings, you can start Python with
`-Wi::Deprecation`. This sets all deprecation warnings to ignored. There is
also an Astropy-specific [`AstropyDeprecationWarning`](api/astropy.utils.exceptions.AstropyDeprecationWarning.html#astropy.utils.exceptions.AstropyDeprecationWarning "astropy.utils.exceptions.AstropyDeprecationWarning")
which can be used to disable deprecation warnings from Astropy only.

See [the CPython documentation](https://docs.python.org/3/using/cmdline.html#cmdoption-W) for more
information on the -W argument.