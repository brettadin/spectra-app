```
>>> from astroquery.vamdc import Vamdc
>>> ch3oh = Vamdc.query_molecule('CH3OH')
>>> from vamdclib import specmodel
>>> partition_func = specmodel.calculate_partitionfunction(ch3oh.data['States'],
                                                           temperature=100)
>>> print(partition_func)
{'XCDMS-149': 1185.5304044622881}
```