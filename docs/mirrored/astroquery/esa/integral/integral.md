```
>>> from astroquery.esa.integral import IntegralClass
>>> isla = IntegralClass()
>>> metadata = isla.get_source_metadata(target_name='Crab')
>>> metadata
[{'name': 'Integral', 'link': None, 'metadata': [{'param': 'Name', 'value': 'Crab'}, {'param': 'Id', 'value': 'J053432.0+220052'}, {'param': 'Coordinates degrees', 'value': '83.6324 22.0174'}, {'param': 'Coordinates', 'value': '05 34 31.78 22 01 02.64'}, {'param': 'Galactic', 'value': '184.55 -5.78'}, {'param': 'Isgri flag2', 'value': 'very bright source'}, {'param': 'Jemx flag', 'value': 'detected'}, {'param': 'Spi flag', 'value': 'detected'}, {'param': 'Picsit flag', 'value': 'detected'}]}, {'name': 'Simbad', 'link': 'https://simbad.cds.unistra.fr/simbad/sim-id?Ident=Crab', 'metadata': [{'param': 'Id', 'value': 'NAME Crab'}, {'param': 'Type', 'value': 'SuperNova Remnant'}, {'param': 'Other types', 'value': 'HII|IR|Psr|Rad|SNR|X|gam'}]}]
```