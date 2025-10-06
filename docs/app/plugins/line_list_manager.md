# Line list manager plugin

The line list manager detects prominent emission and absorption features using the specutils derivative algorithm and plots diagnostic markers as a derived overlay. It aligns with the SpecViz line list manager plugin by pairing detection thresholds with customizable marker styling and keeping the catalog exportable for offline analysis.[^specviz-plugins]

## Controls
- **Flux threshold (σ)** – minimum derivative significance required to register a line.
- **Marker width (nm)** – half-width of the triangular markers rendered around each detection.
- **Dataset picker** – choose a single spectrum to analyse.

## Outputs
- Optional “Detected lines” overlay populated with triangular markers and hover tooltips.
- A detection table (wavelength, line type) stored via the manifest pipeline for provenance and downstream filtering.

[^specviz-plugins]: SpecViz plugin catalog — https://github.com/spacetelescope/jdaviz/blob/main/docs/specviz/plugins.rst
