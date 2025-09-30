```
>>> from pprint import pprint
>>> from astroquery.mast import Mast
>>> mast = Mast()
...
>>> # Resolve a single object
>>> coords = mast.resolve_object("M101", resolver="NED")
>>> print(coords)
<SkyCoord (ICRS): (ra, dec) in deg
    (210.80227, 54.34895)>
...
>>> # Resolve multiple objects
>>> coords_multi = mast.resolve_object(["M101", "M51"], resolver="SIMBAD")
>>> pprint(coords_multi)
{'M101': <SkyCoord (ICRS): (ra, dec) in deg
    (210.802429, 54.34875)>,
 'M51': <SkyCoord (ICRS): (ra, dec) in deg
    (202.469575, 47.195258)>}
...
>>> # Resolve a single object with all resolvers
>>> coords_dict = mast.resolve_object("M101", resolve_all=True)
>>> pprint(coords_dict)
{'NED': <SkyCoord (ICRS): (ra, dec) in deg
    (210.80227, 54.34895)>,
 'SIMBAD': <SkyCoord (ICRS): (ra, dec) in deg
    (210.802429, 54.34875)>,
 'SIMBADCFA': <SkyCoord (ICRS): (ra, dec) in deg
    (210.802429, 54.34875)>}
...
>>> # Resolve multiple objects with all resolvers
>>> coords_dict_multi = mast.resolve_object(["M101", "M51"], resolve_all=True)
>>> pprint(coords_dict_multi)
{'M101': {'NED': <SkyCoord (ICRS): (ra, dec) in deg
   (210.80227, 54.34895)>,
         'SIMBAD': <SkyCoord (ICRS): (ra, dec) in deg
   (210.802429, 54.34875)>,
         'SIMBADCFA': <SkyCoord (ICRS): (ra, dec) in deg
   (210.802429, 54.34875)>},
'M51': {'NED': <SkyCoord (ICRS): (ra, dec) in deg
   (202.48417, 47.23056)>,
         'SIMBAD': <SkyCoord (ICRS): (ra, dec) in deg
   (202.469575, 47.195258)>,
         'SIMBADCFA': <SkyCoord (ICRS): (ra, dec) in deg
   (202.469575, 47.195258)>}}
```