# Exporting & Sharing

Exports capture the exact view shown in the UI and record every transformation applied to the spectra. The export stack is implemented in `app/export_manifest.py`.

## Export Formats
When you click **Export what I see**, the app writes three artefacts into a timestamped directory:
1. **PNG** — the Plotly figure exactly as displayed (including zoom level and visible traces).
2. **CSV** — numerical data for all visible traces rebinned to the displayed grid.
3. **JSON manifest** — machine-readable metadata describing sources, unit conversions, and processing steps.

## Manifest Contents
Each manifest includes:
- Export timestamp and app version (`v1.1.5b`).
- A `continuity` block referencing the brains log, patch notes, AI handoff bridge, and provider directories.
- Entries per trace with:
  - Original file name and SHA-256 hash.
  - Original units vs. canonical units.
  - Conversions applied (`F_ν → F_λ`, wavelength scaling, uncertainty propagation).
  - Resolution changes and rebinning parameters.
  - Metadata (instrument, telescope, observation date, observer, provenance notes).
- Plot state (axis ranges, whether emission/absorption axes were used, and toggled traces).

## Reproducing an Export
1. Clone the repository at the commit hash listed in the manifest.
2. Place uploaded files in the same relative paths or fetch them using the recorded hashes.
3. Run `streamlit run app/ui/main.py`.
4. Use the manifest to reapply processing steps or to verify that the displayed spectrum matches your source data.

## Sharing Guidelines
- Always bundle the manifest with the PNG/CSV when sharing results so collaborators can trace unit conversions.
- Use the SHA-256 hash to confirm file integrity before rerunning an analysis.
- If you adjust the export manually (e.g., annotate the PNG), note the changes in a lab notebook or commit message—the manifest should remain untouched.

## Troubleshooting
| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| Exported PNG is blank | The figure had no visible traces. | Ensure at least one trace is active in the legend before exporting. |
| CSV missing uncertainty column | Source file did not provide uncertainties or they were filtered during ingestion. | Re-upload with an `_err` column or use the manifest to confirm the pipeline dropped it intentionally. |
| Manifest missing metadata | FITS headers lacked the relevant keywords. | Manually supplement metadata when sharing, and consider updating the source file’s headers. |

Exports are deterministic: running the same data through the same commit produces identical PNG, CSV, and manifest files aside from timestamps.
