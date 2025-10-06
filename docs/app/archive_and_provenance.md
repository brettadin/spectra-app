# Archive lookups and provenance

Spectra App connects to several provider stubs so you can experiment with
lookups without leaving the UI.

## Archive lookups

The **Archive** tab exposes a consistent search experience across providers.
Enter a target, instrument, and max results. For the offline stubs included with
this build, results are deterministic so you can rehearse the workflow. Each hit
includes a summary and an **Add overlay** action that pipes the spectrum back
into the overlay workspace.

## Provenance tracking

Every fetched or uploaded trace accumulates provenance metadata:

- Source archive and fetch parameters.
- Instrument, telescope, and observation date when available.
- Unit conversion and normalization steps performed inside the app.

The metadata summary expander on the overlay tab and the session provenance
section inside **Docs & provenance** show the same information. Export manifests
bundle these fields so downstream analysis can audit decisions made in the app.

## Tips for real datasets

- Prefer fetching both the science spectrum and calibration frames so you can
  compare them differentially later.
- Record the resolver query (SIMBAD, etc.) that led you to the archive record.
- Keep the provenance JSON alongside any exported CSV/PNG artifacts. It is the
  authoritative source for how the trace was prepared in-app.
