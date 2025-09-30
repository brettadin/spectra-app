```
>>> distr.shape
(4,)
>>> distr.size
4
>>> distr.unit
Unit("ct")
>>> distr.n_samples
1000
>>> distr.pdf_mean()
<Quantity [  1.034,   5.026,  29.994, 400.365] ct>
>>> distr.pdf_std()
<Quantity [ 1.04539179,  2.19484031,  5.47776998, 19.87022333] ct>
>>> distr.pdf_var()
<Quantity [  1.092844,   4.817324,  30.005964, 394.825775] ct2>
>>> distr.pdf_median()
<Quantity [   1.,   5.,  30., 400.] ct>
>>> distr.pdf_mad()  # Median absolute deviation
<Quantity [ 1.,  1.,  4., 13.] ct>
>>> distr.pdf_smad()  # Median absolute deviation, rescaled to match std for normal
<Quantity [ 1.48260222,  1.48260222,  5.93040887, 19.27382884] ct>
>>> distr.pdf_percentiles([10, 50, 90])
<Quantity [[  0. ,   2. ,  23. , 375. ],
           [  1. ,   5. ,  30. , 400. ],
           [  2. ,   8. ,  37. , 426.1]] ct>
>>> distr.pdf_percentiles([.1, .5, .9]*u.dimensionless_unscaled)
<Quantity [[  0. ,   2. ,  23. , 375. ],
          [  1. ,   5. ,  30. , 400. ],
          [  2. ,   8. ,  37. , 426.1]] ct>
```