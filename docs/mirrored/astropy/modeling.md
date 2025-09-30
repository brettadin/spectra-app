```
import numpy as np
import matplotlib.pyplot as plt
from astropy.modeling import models, fitting

# define a model for a line
line_orig = models.Linear1D(slope=1.0, intercept=0.5)

# generate x, y data non-uniformly spaced in x
# add noise to y measurements
npts = 30
rng = np.random.default_rng(10)
x = rng.uniform(0.0, 10.0, npts)
y = line_orig(x)
y += rng.normal(0.0, 1.5, npts)

# initialize a linear fitter
fit = fitting.LinearLSQFitter()

# initialize a linear model
line_init = models.Linear1D()

# fit the data with the fitter
fitted_line = fit(line_init, x, y)

# plot the model
fig, ax = plt.subplots()
ax.plot(x, y, 'ko', label='Data')
ax.plot(x, fitted_line(x), 'k-', label='Fitted Model')
ax.set(xlabel='x', ylabel='y')
ax.legend()
```