### Querying the catalog

The default option to return the query payload is set to `False`. In the
following examples we have explicitly set it to False and True to show the what
each setting yields:

```
>>> from astroquery.linelists.cdms import CDMS
>>> import astropy.units as u
>>> response = CDMS.query_lines(min_frequency=100 * u.GHz,
...                             max_frequency=1000 * u.GHz,
...                             min_strength=-500,
...                             molecule="028503 CO",
...                             get_query_payload=False)
>>> response.pprint(max_width=120)
     FREQ     ERR    LGINT   DR   ELO    GUP MOLWT TAG QNFMT  Ju  Ku  vu F1u F2u F3u  Jl  Kl  vl F1l F2l F3l   name  Lab
     MHz      MHz   nm2 MHz      1 / cm        u
 ----------- ------ ------- --- -------- --- ----- --- ----- --- --- --- --- --- --- --- --- --- --- --- --- ------- ----
 115271.2018 0.0005 -5.0105   2      0.0   3    28 503   101   1  --  --  --  --  --   0  --  --  --  --  -- CO, v=0 True
    230538.0 0.0005 -4.1197   2    3.845   5    28 503   101   2  --  --  --  --  --   1  --  --  --  --  -- CO, v=0 True
 345795.9899 0.0005 -3.6118   2   11.535   7    28 503   101   3  --  --  --  --  --   2  --  --  --  --  -- CO, v=0 True
 461040.7682 0.0005 -3.2657   2  23.0695   9    28 503   101   4  --  --  --  --  --   3  --  --  --  --  -- CO, v=0 True
 576267.9305 0.0005 -3.0118   2  38.4481  11    28 503   101   5  --  --  --  --  --   4  --  --  --  --  -- CO, v=0 True
 691473.0763 0.0005 -2.8193   2  57.6704  13    28 503   101   6  --  --  --  --  --   5  --  --  --  --  -- CO, v=0 True
  806651.806  0.005 -2.6716   2  80.7354  15    28 503   101   7  --  --  --  --  --   6  --  --  --  --  -- CO, v=0 True
    921799.7  0.005  -2.559   2 107.6424  17    28 503   101   8  --  --  --  --  --   7  --  --  --  --  -- CO, v=0 True
```

The following example, with `get_query_payload = True`, returns the payload:

```
>>> response = CDMS.query_lines(min_frequency=100 * u.GHz,
...                             max_frequency=1000 * u.GHz,
...                             min_strength=-500,
...                             molecule="028503 CO",
...                             get_query_payload=True)
>>> print(response)
{'MinNu': 100.0, 'MaxNu': 1000.0, 'UnitNu': 'GHz', 'StrLim': -500, 'temp': 300, 'logscale': 'yes', 'mol_sort_query': 'tag', 'sort': 'frequency', 'output': 'text', 'but_action': 'Submit', 'Molecules': '028503 CO'}
```

The units of the columns of the query can be displayed by calling
`response.info`:

```
>>> response = CDMS.query_lines(min_frequency=100 * u.GHz,
...                             max_frequency=1000 * u.GHz,
...                             min_strength=-500,
...                             molecule="028503 CO",
...                             get_query_payload=False)
>>> print(response.info)
<Table length=8>
 name  dtype    unit     class     n_bad
----- ------- ------- ------------ -----
 FREQ float64     MHz       Column     0
  ERR float64     MHz       Column     0
LGINT float64 nm2 MHz       Column     0
   DR   int64               Column     0
  ELO float64  1 / cm       Column     0
  GUP   int64               Column     0
MOLWT   int64       u       Column     0
  TAG   int64               Column     0
QNFMT   int64               Column     0
   Ju   int64               Column     0
   Ku   int64         MaskedColumn     8
   vu   int64         MaskedColumn     8
  F1u   int64         MaskedColumn     8
  F2u   int64         MaskedColumn     8
  F3u   int64         MaskedColumn     8
   Jl   int64               Column     0
   Kl   int64         MaskedColumn     8
   vl   int64         MaskedColumn     8
  F1l   int64         MaskedColumn     8
  F2l   int64         MaskedColumn     8
  F3l   int64         MaskedColumn     8
 name    str7               Column     0
  Lab    bool               Column     0
```

These come in handy for converting to other units easily, an example using a
simplified version of the data above is shown below:

```
>>> print(response['FREQ', 'ERR', 'ELO'])
     FREQ     ERR     ELO
     MHz      MHz    1 / cm
 ----------- ------ --------
 115271.2018 0.0005      0.0
    230538.0 0.0005    3.845
 345795.9899 0.0005   11.535
 461040.7682 0.0005  23.0695
 576267.9305 0.0005  38.4481
 691473.0763 0.0005  57.6704
  806651.806  0.005  80.7354
    921799.7  0.005 107.6424
>>> response['FREQ'].quantity
 <Quantity [115271.2018, 230538.    , 345795.9899, 461040.7682, 576267.9305,
            691473.0763, 806651.806 , 921799.7   ] MHz>
>>> response['FREQ'].to('GHz')
 <Quantity [115.2712018, 230.538    , 345.7959899, 461.0407682, 576.2679305,
            691.4730763, 806.651806 , 921.7997   ] GHz>
```

The parameters and response keys are described in detail under the
Reference/API section.

### Looking Up More Information from the partition function file

If you have found a molecule you are interested in, the `tag` column in the
results provides enough information to access specific molecule information
such as the partition functions at different temperatures. Keep in mind that a
negative `tag` value signifies that the line frequency has been measured in the
laboratory but not in space

```
>>> import matplotlib.pyplot as plt
>>> from astroquery.linelists.cdms import CDMS
>>> result = CDMS.get_species_table()
>>> mol = result[result['tag'] == 28503]
>>> mol.pprint(max_width=160)
 tag  molecule    Name   #lines lg(Q(1000)) lg(Q(500)) lg(Q(300)) ... lg(Q(9.375)) lg(Q(5.000)) lg(Q(2.725)) Ver. Documentation Date of entry    Entry
----- -------- --------- ------ ----------- ---------- ---------- ... ------------ ------------ ------------ ---- ------------- ------------- -----------
28503  CO, v=0 CO, v = 0     95      2.5595     2.2584     2.0369 ...       0.5733       0.3389       0.1478    1   e028503.cat     Oct. 2000 w028503.cat
```

One of the advantages of using CDMS is the availability in the catalog of the
partition function at different temperatures for the molecules (just like for
JPL). As a continuation of the example above, an example that accesses and
plots the partition function against the temperatures found in the metadata is
shown below:

```
>>> import numpy as np
>>> keys = [k for k in mol.keys() if 'lg' in k]
>>> temp = np.array([float(k.split('(')[-1].split(')')[0]) for k in keys])
>>> part = list(mol[keys][0])
>>> plt.scatter(temp, part)
>>> plt.xlabel('Temperature (K)')
>>> plt.ylabel('Partition Function Value')
>>> plt.title('Partition Function vs Temperature')
```

([`Source code`](../../_downloads/54c56040166e6740d3ea8b5417ff9097/cdms-1.py), [`png`](../../_downloads/f1b71ed1c79c49d4954b3b072291c286/cdms-1.png), [`hires.png`](../../_downloads/35a4829fe03cfd79999be47abd8fb724/cdms-1.hires.png), [`pdf`](../../_downloads/a7339d3b283e1f3a3af85469df54c097/cdms-1.pdf))

![../../_images/cdms-1.png](../../_images/cdms-1.png)

For non-linear molecules like H2CO, curve fitting methods can be used to
calculate production rates at different temperatures with the proportionality:
`a*T**(3./2.)`. Calling the process above for the H2CO molecule (instead of
for the CO molecule) we can continue to determine the partition function at
other temperatures using curve fitting models:

```
>>> import numpy as np
>>> import matplotlib.pyplot as plt
>>> from astroquery.linelists.cdms import CDMS
>>> from scipy.optimize import curve_fit
...
>>> result = CDMS.get_species_table()
>>> mol = result[result['tag'] == 30501] #do not include signs of tag for this
...
>>> def f(T, a):
        return np.log10(a*T**(1.5))
>>> keys = [k for k in mol.keys() if 'lg' in k]
>>> def tryfloat(x):
...     try:
...        return float(x)
...     except:
...        return np.nan
>>> temp = np.array([float(k.split('(')[-1].split(')')[0]) for k in keys])
>>> part = np.array([tryfloat(x) for x in mol[keys][0]])
>>> param, cov = curve_fit(f, temp[np.isfinite(part)], part[np.isfinite(part)])
>>> print(param)
# array([0.51865074])
>>> x = np.linspace(2.7,500)
>>> y = f(x,param[0])
>>> plt.scatter(temp,part,c='r')
>>> plt.plot(x,y,'k')
>>> plt.title('Partition Function vs Temperature')
>>> plt.xlabel('Temperature')
>>> plt.ylabel('Log10 of Partition Function')
```

([`Source code`](../../_downloads/b16ffe4ef69ed6376af303b36464cda6/cdms-2.py), [`png`](../../_downloads/31f8e851e17fc032c2b7a3b0c1f977ce/cdms-2.png), [`hires.png`](../../_downloads/5de65dcf346609671138ed2b6d42d980/cdms-2.hires.png), [`pdf`](../../_downloads/e034f47528418f538c25fc7598e18d45/cdms-2.pdf))

![../../_images/cdms-2.png](../../_images/cdms-2.png)

We can then compare linear interpolation to the fitted interpolation above:

```
>>> interp_Q = np.interp(x, temp, 10**part)
>>> plt.plot(x, (10**y-interp_Q)/10**y)
>>> plt.xlabel("Temperature")
>>> plt.ylabel("Fractional difference between linear and fitted")
```

([`Source code`](../../_downloads/454a147768be33506fd14dafe4b41e0b/cdms-3.py), [`png`](../../_downloads/1fa66193f75fab29a5daaff048cf84f7/cdms-3.png), [`hires.png`](../../_downloads/40a156fcd02d52cbc10a90a4648a2a50/cdms-3.hires.png), [`pdf`](../../_downloads/4b33a9c54f9dd793c1572054ffca1111/cdms-3.pdf))

![../../_images/cdms-3.png](../../_images/cdms-3.png)

Linear interpolation is a good approximation, in this case, for any moderately
high temperatures, but is increasingly poor at lower temperatures.
It can be valuable to check this for any given molecule.