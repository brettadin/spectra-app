`astropy.io` provides type annotations through the [`astropy.io.typing`](#module-astropy.io.typing "astropy.io.typing") module.
These type annotations allow users to specify the expected types of variables, function
parameters, and return values when working with I/O. By using type annotations,
developers can improve code readability, catch potential type-related errors early, and
enable better code documentation and tooling support.

For example, the following function uses type annotations to specify that the
`filename` parameter can be any type of path-like object (e.g. a string, byte-string,
or pathlib.Path object).

```
from astropy.io import fits
from astropy.io.typing import PathLike

def read_fits_file(filename: PathLike) -> fits.HDUList:
     return fits.open(filename)
```

The [`astropy.io.typing`](#module-astropy.io.typing "astropy.io.typing") module also provides type aliases for file-like objects
that support reading and writing. The following example uses the
[`ReadableFileLike`](../api/astropy.io.typing.ReadableFileLike.html#astropy.io.typing.ReadableFileLike "astropy.io.typing.ReadableFileLike") type alias to specify that the `fileobj`
parameter can be any file-like object that supports reading. Using a
[`TypeVar`](https://docs.python.org/3/library/typing.html#typing.TypeVar "(in Python v3.13)"), the return type of the function is specified to be the same
type as the file-like object can read.

```
from typing import TypeVar
from astropy.io.typing import ReadableFileLike

R = TypeVar('R')  # type of object returned by fileobj.read()

def read_from_file(fileobj: ReadableFileLike[R]) -> R:
     """Reads from a file-like object and returns the result."""
     return fileobj.read()
```

## Reference/API

### astropy.io.typing Module

Type annotations for `astropy.io`.

These are type annotations for I/O-related functions and classes. Some of the type
objects can also be used as runtime-checkable [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol "(in Python v3.13)") objects.

#### Class Inheritance Diagram

Inheritance diagram of astropy.io.typing.ReadableFileLike, astropy.io.typing.WriteableFileLike