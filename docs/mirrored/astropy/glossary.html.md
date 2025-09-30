(`n`,)
:   A parenthesized number followed by a comma denotes a tuple with one
    element. The trailing comma distinguishes a one-element tuple from a
    parenthesized `n`.
    This is from NumPy; see <https://numpy.org/doc/stable/glossary.html#term-n>.

-like
:   `<Class>-like` is an instance of the `Class` or a valid initializer argument
    for `Class` as `Class(value)`. E.g. [`Quantity`](api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity")-like
    includes `"2 * u.km"` because `astropy.units.Quantity("2 * u.km")` works.

[‘physical type’]
:   The physical type of a quantity can be annotated in square brackets
    following a [`Quantity`](api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity") (or similar [quantity-like](#term-quantity-like)).

    For example, `distance : quantity-like ['length']`

angle-like
:   [quantity-like](#term-quantity-like) and a valid initializer for [`Angle`](api/astropy.coordinates.Angle.html#astropy.coordinates.Angle "astropy.coordinates.Angle").
    The `unit` must be an angular. A string input is interpreted as an angle as
    described in the [`Angle`](api/astropy.coordinates.Angle.html#astropy.coordinates.Angle "astropy.coordinates.Angle") documentation.

buffer-like
:   Object that implements [Python’s buffer protocol](https://docs.python.org/3/c-api/buffer.html#bufferobjects).

coordinate-like
:   [`BaseCoordinateFrame`](api/astropy.coordinates.BaseCoordinateFrame.html#astropy.coordinates.BaseCoordinateFrame "astropy.coordinates.BaseCoordinateFrame") subclass instance, or a
    [`SkyCoord`](api/astropy.coordinates.SkyCoord.html#astropy.coordinates.SkyCoord "astropy.coordinates.SkyCoord") (or subclass) instance, or a valid
    initializer as described in [COORD](coordinates/skycoord.html#coordinates-initialization-coord).

file-like (readable)
:   [file-like object](https://docs.python.org/3/glossary.html#term-file-like-object "(in Python v3.13)") object that supports reading with a method `read`.

    For a formal definition see [`ReadableFileLike`](api/astropy.io.typing.ReadableFileLike.html#astropy.io.typing.ReadableFileLike "astropy.io.typing.ReadableFileLike").

file-like (writeable)
:   [file-like object](https://docs.python.org/3/glossary.html#term-file-like-object "(in Python v3.13)") object that supports writing with a method `write`.

    For a formal definition see [`WriteableFileLike`](api/astropy.io.typing.WriteableFileLike.html#astropy.io.typing.WriteableFileLike "astropy.io.typing.WriteableFileLike").

frame-like
:   [`BaseCoordinateFrame`](api/astropy.coordinates.BaseCoordinateFrame.html#astropy.coordinates.BaseCoordinateFrame "astropy.coordinates.BaseCoordinateFrame") subclass or subclass instance or
    a valid Frame name (string).

length-like
:   [quantity-like](#term-quantity-like) and a valid initializer for
    [`Distance`](api/astropy.coordinates.Distance.html#astropy.coordinates.Distance "astropy.coordinates.Distance"). The `unit` must be a convertible to a
    unit of length.

number
:   Any scalar numeric type. e.g. [`float`](https://docs.python.org/3/library/functions.html#float "(in Python v3.13)") or [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") or `numpy.number`.

quantity-like
:   [`Quantity`](api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity") (or subclass) instance, a number or [array-like](https://numpy.org/doc/stable/glossary.html#term-array_like) object, or a string
    which is a valid initializer for [`Quantity`](api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity").

    For a formal definition see [`QuantityLike`](units/type_hints.html#astropy.units.typing.QuantityLike "astropy.units.typing.QuantityLike").

table-like
:   [`Table`](api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") (or subclass) instance or valid initializer for
    [`Table`](api/astropy.table.Table.html#astropy.table.Table "astropy.table.Table") as described in [Constructing a Table](table/construct_table.html#construct-table). Common types
    include `dict[list]`, `list[dict]`, `list[list]`, and [`ndarray`](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html#numpy.ndarray "(in NumPy v2.3)")
    (structured array).

time-like
:   [`Time`](api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time") (or subclass) instance or a valid initializer for
    [`Time`](api/astropy.time.Time.html#astropy.time.Time "astropy.time.Time"), e.g. [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), array-like[str], [`datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.13)"), or
    [`datetime64`](https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.datetime64 "(in NumPy v2.3)").

trait type
:   In short, a trait type is a class with the following properties:

    * It is a class that can be used as a mixin to add functionality to another class.
    * It should never be instantiated directly.
    * It should not be used as a base class for other classes, but only as a mixin.
    * It can define methods, properties, and attributes – any of which can be abstract.
    * It can be generic, i.e. it can have type parameters.
    * It can subclass other traits, but should have a linear MRO.

    These are the same set of properties as orthogonal mixin classes, with the added
    emphasis that they can serve as compiled types, if so enabled by a compilation system such as [mypyc](https://mypyc.readthedocs.io/en/latest/).

unit-like
:   [`UnitBase`](api/astropy.units.UnitBase.html#astropy.units.UnitBase "astropy.units.UnitBase") subclass instance or a valid initializer for
    [`Unit`](api/astropy.units.Unit.html#astropy.units.Unit "astropy.units.Unit"), e.g., [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") or scalar [`Quantity`](api/astropy.units.Quantity.html#astropy.units.Quantity "astropy.units.Quantity").