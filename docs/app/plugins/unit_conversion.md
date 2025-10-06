# Unit conversion plugin

The unit conversion plugin duplicates selected spectra with flux rescaled into a user-selected Astropy unit. This reproduces the SpecViz unit conversion workflow, allowing analysts to toggle between Jansky, cgs, or SI flux conventions without mutating the original data layer.[^specviz-plugins]

## Controls
- **Target flux unit** – dropdown of vetted Astropy units (Jy, erg cm⁻² s⁻¹ Å⁻¹, erg cm⁻² s⁻¹ nm⁻¹, W m⁻² µm⁻¹).
- **Dataset picker** – choose one or more spectra from the overlay tray.

## Outputs
- New overlays tagged with the converted unit and linked to the source trace in provenance metadata.
- A unit conversion table exported to the manifest pipeline capturing original and converted flux units for each trace.

[^specviz-plugins]: SpecViz plugin catalog — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
