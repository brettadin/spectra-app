# Data Ingestion Pipeline

The ingestion pipeline ensures every spectrum—whether uploaded by a user or fetched from a provider—uses consistent SI units before rendering. The logic lives in `app/server/ingestion_pipeline.py` and is covered by `tests/test_continuity.py`.

## Pipeline Overview
1. **Parse input** from CSV/TXT/FITS or built-in samples.
2. **Detect units** using FITS headers (`CUNIT1`, `BUNIT`, etc.) or column names (e.g., `wavelength_nm`, `flux_mJy`).
3. **Convert wavelengths to metres** and fluxes to `F_λ` (per metre).
4. **Infer native resolving power** from header metadata (`CDELT1`, `CRVAL1`) or sample spacing.
5. **Convolve** to the requested display resolution when the user toggles the resolution control.
6. **Rebin** onto a logarithmic wavelength grid so zooming and comparisons remain stable.
7. **Store provenance** for every transformation so exports can describe what happened.

## Unit Normalisation
All wavelengths are converted to metres using the detector’s native units:
- **Ångström (`Å`)** → multiply by `1e-10`.
- **Nanometre (`nm`)** → multiply by `1e-9`.
- **Micron (`µm`)** → multiply by `1e-6`.
- **Frequency-based inputs (`Hz`)** → first convert to wavelength via `λ = c / ν` before continuing.

Fluxes are expressed as `F_λ` (e.g., W·m⁻³). When inputs arrive as `F_ν`, the pipeline converts them using:
```
F_ν = F_λ · λ² / c
F_λ = F_ν · c / λ²
```
The provenance log captures the original units, detected form (`F_λ` vs. `F_ν`), and the formula applied.

## Resolution Handling
If the source data includes dispersion keywords (`CDELT1`, `CD1_1`, etc.), the pipeline calculates the instrument’s resolving power `R = λ / Δλ`. When the user selects a target resolution, the pipeline applies a Gaussian convolution kernel in wavelength space. The manifest records:
- native resolution and keywords used to compute it,
- target resolution (if any),
- kernel full width at half maximum (FWHM).

## Logarithmic Rebinning
After convolution, spectra are rebinned onto a log-uniform wavelength grid so overlays align even when sources span different wavelength ranges. The rebinning preserves integrated flux by weighting each sample over its bin width. Metadata stored per trace includes:
- grid bounds (`λ_min`, `λ_max`),
- number of bins,
- interpolation strategy (currently cubic spline with flux-conserving weights).

## Error Propagation
When the input provides uncertainties, they are converted alongside the flux values. Variances propagate through the convolution and rebinning steps, ensuring the uncertainty band displayed in the UI remains accurate.

## Where the Data Goes Next
The processed spectrum is handed to the plotting layer as a `ProcessedSpectrum` object containing:
- normalised arrays (`wavelength_m`, `flux_lambda`, optional `uncertainty_lambda`),
- metadata (instrument, telescope, observation date, native resolution),
- provenance steps (unit conversions, smoothing, rebinning).

The UI stores these objects in session state for toggling overlays, exports them via `app/export_manifest.py`, and displays their metadata beneath the plot.
