```
>>> S = Splatalogue(energy_max=500,
...    energy_type='eu_k', energy_levels=['Four'],
...    line_strengths=['CDMSJPL'])
>>> def trimmed_query(*args,**kwargs):
...     columns = ('species_id', 'chemical_name', 'name', 'resolved_QNs',
...                'orderedfreq',
...                'aij',
...                'upper_state_energy_K')
...     table = S.query_lines(*args, **kwargs)[columns]
...     table.sort('upper_state_energy_K')
...     return table
>>> trimmed_query(1*u.GHz,30*u.GHz,
...     chemical_name='(H2.*Formaldehyde)|( HDCO )',
...     energy_max=50)[:10].pprint(max_width=150)
species_id chemical_name             name                     resolved_QNs         orderedfreq   aij    upper_state_energy_K
---------- ------------- ---------------------------- ---------------------------- ----------- -------- --------------------
       109  Formaldehyde                         HDCO       1(  1, 0)-   1(  1, 1)    5346.142 -8.44112             11.18258
       109  Formaldehyde                         HDCO           1( 1, 0)- 1( 1, 1)   5346.1616 -8.31295             11.18287
       109  Formaldehyde                         HDCO              1(1,0) - 1(1,1)   5346.1416 -8.31616             11.18301
       155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O       1(  1, 0)-   1(  1, 1)    4388.797 -8.22052             15.30187
       155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 1- 0   4388.7783  -9.0498             15.30206
       155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 0- 1   4388.7957 -8.57268             15.30206
       155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 2- 2   4388.7965 -8.69765             15.30206
       155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O              1(1,0) - 1(1,1)    4388.797 -8.57272             15.30206
       155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 2- 1   4388.8012 -9.17475             15.30206
       155  Formaldehyde H<sub>2</sub>C<sup>18</sup>O  1( 1, 0)- 1( 1, 1), F= 1- 2   4388.8036  -8.9529             15.30206
```