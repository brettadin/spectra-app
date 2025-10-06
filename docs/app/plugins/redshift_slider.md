# Redshift slider plugin

The redshift slider duplicates a selected spectrum with wavelengths scaled by *(1 + z)* (or divided when shifting to rest). This reproduces the SpecViz redshift control by letting users preview rest-frame corrections and overlay offset line lists without altering the source data.[^specviz-plugins]

## Controls
- **Redshift z** – slider covering blueshift to high-redshift regimes.
- **Shift to rest frame** – checkbox that applies the inverse scaling (divide by 1 + z).
- **Dataset picker** – choose a single spectrum.

## Outputs
- A redshifted or rest-frame overlay that inherits flux data from the source trace.
- A manifest table recording the z value and rest-frame toggle so exports preserve the applied transformation.

[^specviz-plugins]: SpecViz plugin catalog — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
