# Model fitting plugin

The model fitting plugin fits a single-component Gaussian model to the selected spectrum using specutils and Astropy modelling, surfacing best-fit parameters and a synthetic overlay. This mirrors the SpecViz model fitting experience while exporting parameter tables for provenance and downstream modelling.[^specviz-plugins]

## Controls
- **Initial amplitude** – starting guess for the Gaussian amplitude in flux units.
- **Initial centre (nm)** – initial wavelength guess.
- **Initial σ (nm)** – initial width guess.
- **Dataset picker** – choose a single spectrum.

## Outputs
- A fitted Gaussian overlay sampled on the original wavelength grid.
- A parameter table (amplitude, centre, σ) persisted via the export manifest for traceability.
- Provenance metadata capturing the input guesses and fitted values for each execution.

[^specviz-plugins]: SpecViz plugin catalog — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
