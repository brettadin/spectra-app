```
>>> from astroquery.mpc import MPC
>>> from pprint import pprint
>>> result = MPC.query_object('asteroid', name='ceres')
>>> pprint(result)
[{'absolute_magnitude': '3.52',
  'aphelion_distance': '2.982',
  'arc_length': 80185,
  'argument_of_perihelion': '73.73165',
  'ascending_node': '80.2869866',
  'critical_list_numbered_object': False,
  'delta_v': 10.5,
  'designation': None,
  'earth_moid': 1.58537,
  'eccentricity': '0.0775571',
  'epoch': '2020-05-31.0',
  'epoch_jd': '2459000.5',
  'first_observation_date_used': '1801-01-01.0',
  'first_opposition_used': '1801',
  'inclination': '10.58862',
  'jupiter_moid': 2.09127,
  'km_neo': False,
  'last_observation_date_used': '2020-07-17.0',
  'last_opposition_used': '2020',
  'mars_moid': 0.93178,
  'mean_anomaly': '162.68618',
  'mean_daily_motion': '0.21406',
  'mercury_moid': 2.1761,
  'name': 'Ceres',
  'neo': False,
  'number': 1,
  'observations': 7663,
  'oppositions': 119,
  'orbit_type': 0,
  'orbit_uncertainty': '0',
  'p_vector_x': '-0.88282454',
  'p_vector_y': '0.3292319',
  'p_vector_z': '0.33500327',
  'perihelion_date': '2018-05-01.99722',
  'perihelion_date_jd': '2458240.49722',
  'perihelion_distance': '2.5530055',
  'period': '4.6',
  'pha': False,
  'phase_slope': '0.15',
  'q_vector_x': '-0.43337703',
  'q_vector_y': '-0.84597284',
  'q_vector_z': '-0.3106675',
  'residual_rms': '0.51',
  'saturn_moid': 6.37764,
  'semimajor_axis': '2.7676568',
  'tisserand_jupiter': 3.3,
  'updated_at': '2021-01-16T13:32:57Z',
  'uranus_moid': 15.8216,
  'venus_moid': 1.8382}]
>>> eph = MPC.get_ephemeris('ceres')
>>> print(eph)
          Date                   RA         ... Uncertainty 3sig Unc. P.A.
                                deg         ...      arcsec         deg
----------------------- ------------------- ... ---------------- ---------
2021-01-29 03:16:34.000   355.2416666666667 ...               --        --
2021-01-30 03:16:34.000           355.56125 ...               --        --
2021-01-31 03:16:34.000   355.8812499999999 ...               --        --
2021-02-01 03:16:34.000   356.2029166666666 ...               --        --
2021-02-02 03:16:34.000   356.5254166666666 ...               --        --
2021-02-03 03:16:34.000   356.8491666666667 ...               --        --
2021-02-04 03:16:34.000           357.17375 ...               --        --
2021-02-05 03:16:34.000   357.4995833333333 ...               --        --
2021-02-06 03:16:34.000           357.82625 ...               --        --
2021-02-07 03:16:34.000  358.15374999999995 ...               --        --
2021-02-08 03:16:34.000  358.48249999999996 ...               --        --
2021-02-09 03:16:34.000   358.8120833333333 ...               --        --
2021-02-10 03:16:34.000   359.1429166666666 ...               --        --
2021-02-11 03:16:34.000  359.47416666666663 ...               --        --
2021-02-12 03:16:34.000   359.8066666666666 ...               --        --
2021-02-13 03:16:34.000 0.13999999999999999 ...               --        --
2021-02-14 03:16:34.000  0.4741666666666666 ...               --        --
2021-02-15 03:16:34.000             0.80875 ...               --        --
2021-02-16 03:16:34.000  1.1445833333333333 ...               --        --
2021-02-17 03:16:34.000  1.4812499999999997 ...               --        --
2021-02-18 03:16:34.000  1.8183333333333331 ...               --        --
```