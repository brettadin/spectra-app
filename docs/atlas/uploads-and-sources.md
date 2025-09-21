# Uploads & Built-in Sources

The Spectra App accepts laboratory lamps, archival references, and your own observations. This guide explains how to ingest each source and manage overlays without duplicating data.

## Supported File Types
| Extension | Expected Content | Notes |
| --- | --- | --- |
| `.fits` | Spectra stored in primary or extension HDUs | Uses `astropy.io.fits` to read headers and data arrays. Multiple spectral segments are processed individually and can be toggled in the UI. |
| `.csv` | Delimited text with headers | Required columns: wavelength + flux. Optional: uncertainty. Unit hints should appear in the column names (e.g., `wavelength_nm`, `flux_mJy`). |
| `.txt` | Plain text with whitespace or comma separators | Treated like CSV. Include a header row or provide units via the upload dialog. |

## Upload Workflow
1. Click **Upload spectra** in the sidebar and drop one or more files (size limit defined by Streamlit configuration).
2. The app hashes the file contents; duplicates are ignored and produce a toast notification.
3. Metadata extracted from FITS headers or CSV columns populates the info panel beneath the plot:
   - `TELESCOPE`, `INSTRUME`, `OBSERVER`
   - Wavelength range
   - Observation date (`DATE-OBS`)
   - Native resolving power and dispersion keywords used
4. Each uploaded segment appears as a toggleable entry in the legend. You can hide or show any trace without removing it from session state.

## Column & Header Detection
- Wavelength columns may use suffixes `_m`, `_nm`, `_angstrom`, `_um`. The ingestion pipeline normalises them to metres.
- Flux columns may include `_flam`, `_fnu`, `_jy`, `_mjy`. The pipeline converts everything to `F_λ`.
- Uncertainty columns follow the pattern `<flux_column>_err` or `<flux_column>_unc` and propagate through processing.

## Handling FITS Segments
If the FITS file contains multiple 1-D spectra (e.g., echelle orders), the uploader processes each extension separately. Segment names are derived from header keywords (`EXTNAME`, `SPEC_ID`, etc.) or fall back to index numbers. The metadata card summarises how many segments loaded and the unit conversions applied per segment.

## Built-in Reference Sources
The sidebar also exposes switchable lamp and solar references:
- Hydrogen, Helium, Neon, Mercury, Xenon lamps
- Solar and telluric templates

Each lamp lives in its own legend entry so you can compare them individually. The metadata card lists the provenance of built-in references and the timestamp when they were bundled with the app.

## Managing Overlays
- Use the **Emission / Absorption** toggles to place traces on the appropriate axis. Emission spectra plot on the positive (left) axis; absorption or transmission data plot on the right axis with mirrored units.
- The legend icons show which axis each trace uses. Hovering over a trace reveals its units.
- The **Hide all uploads** button clears the viewport while keeping uploads in session state; press **Restore** to bring them back without re-uploading.

## Removing Data
To free session memory, click the trash icon next to an upload in the sidebar. The manifest keeps a record of removed traces for reproducibility, including the SHA-256 hash of the original file.
