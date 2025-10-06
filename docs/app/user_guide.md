# Spectra App quick start

Use this guide to get familiar with the refreshed Spectra App workspace and the
core flows for loading, inspecting, and comparing spectra.

## 1. Load reference material

The **Reference spectra** drawer on the left keeps quick actions together:

- **Example overlays** – seeded lamp spectra that behave like real traces. Use
  them to test the workflow before importing your own files.
- **NIST ASD lines** – fetch curated line lists directly from the app by typing
  an element (e.g. `Fe II`) and wavelength bounds. The lines arrive pre-tagged
  with metadata and can be toggled on or off alongside your uploaded spectra.

All traces land in the overlay table with provenance and duplicate controls so
it is always obvious where each series originated.

## 2. Add your own spectra

Drop CSV/TXT/FITS files onto **Upload recorded spectra**. The uploader supports
multiple files at once and records a checksum so accidental duplicates are
flagged. After ingestion you can:

- Toggle visibility per trace.
- Switch the wavelength unit (nm, Å, µm, cm⁻¹) from the sidebar.
- Choose how flux is displayed (raw vs. normalized) without altering your
  source data.

Provenance and unit conversion steps are preserved automatically and surface in
both the metadata expander and export manifest.

## 3. Explore in the overlay tab

Once spectra are loaded, the overlay workspace renders an interactive Plotly
chart with zoom/pan, tooltips, and export controls. Use the sidebar to adjust
normalization or viewport bounds. The similarity panel beneath the chart
summarizes how closely the visible traces match the selected reference.

## 4. Compare spectra differentially

The **Differential** tab aligns two traces on a shared grid and lets you compute
a subtraction or ratio curve. Results appear as a stacked plot and a numeric
summary table, and you can add the derived spectrum back into the overlay view
when it is useful for subsequent comparisons.

## 5. Document and export your work

The **Docs & provenance** tab now focuses on app guidance and session history.
Use it to read task-specific docs, review provenance metadata for each overlay,
or download the latest manifest. When you export the current overlay viewport
as CSV/PNG, the manifest contains the same provenance block so downstream
analysis can be reproduced.
