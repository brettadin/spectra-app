# Gaussian smoothing plugin

The Gaussian smoothing plugin convolves one or more visible spectra with a configurable Gaussian kernel and publishes the result as a new overlay. The control surface mirrors the jdaviz SpecViz “Gaussian Smooth” plugin by exposing a single σ parameter measured in spectral pixels and rendering the output asynchronously so large traces do not block the UI.[^specviz-plugins]

## Controls
- **Kernel σ (pixels)** – slider selecting the Gaussian standard deviation.
- **Dataset picker** – select one or more spectra from the workspace overlay list.

## Outputs
- Smoothed spectra labelled with the kernel setting and recorded in the overlay tray.
- A parameter table summarising the σ value applied to each selected trace.
- Provenance metadata embedded in the overlay payload and export manifest so downstream exports document the smoothing parameters.

[^specviz-plugins]: SpecViz plugin catalog — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
