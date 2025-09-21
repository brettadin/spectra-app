# Visualisation & Analysis

The Spectra App uses Plotly for interactive plots. This article explains how to interpret axes, manipulate the view, and explore metadata.

## Plot Layout
- **Primary Y-Axis (left)** — emission flux in `F_λ` units.
- **Secondary Y-Axis (right)** — absorption depth or transmission, mirrored to keep values positive.
- **Shared X-Axis** — wavelength in metres (displayed with an auto-selected prefix such as nm or µm for readability).

Every trace label includes its axis designation and unit. Hovering over a data point reveals:
- wavelength with unit prefix,
- flux value (emission or absorption),
- uncertainty (if available),
- the spectrum name.

## Interactive Controls
- **Zoom** by dragging a rectangle; double-click to reset.
- **Pan** using the Plotly toolbar.
- **Band Shortcuts** appear above the plot (e.g., Balmer, Paschen). Click to jump to the relevant wavelength range.
- **Toggle traces** using the legend or the sidebar checkboxes. Plotly highlights the active trace for clarity.

## Metadata Panel
Below the plot you will find a dynamic metadata summary for the selected traces:
- Source name, telescope, instrument, observer
- Observation date and wavelength coverage
- Unit conversions applied (original → canonical), including formulas
- Processing steps: convolution kernel, target resolution, rebinning grid
- Any warnings raised during ingestion (e.g., missing uncertainty column)

Use this panel to validate that the plotted data matches your expectations before exporting.

## Comparing Spectra
1. Upload or enable multiple sources.
2. Assign each to emission or absorption as appropriate.
3. Use the legend toggles to isolate one trace at a time or overlay them all.
4. For precise alignment, enable the **Normalise flux** option (when available) so the app scales traces to a common median.

## Handling Negative Flux
If an emission spectrum contains negative values (e.g., due to calibration offsets), the pipeline recentres the baseline but preserves the original values in the provenance log. Absorption spectra intentionally plot on the mirrored axis so the magnitude of the feature remains intuitive.

## Saving Views
Click **Export what I see** to capture the current viewport. The export honours zoom level, trace visibility, and axis ranges. Refer to [Exporting & Sharing](exporting-and-sharing.md) for details on the manifest.
