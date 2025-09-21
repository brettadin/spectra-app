# CSV_FITS_INGEST_SPEC (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:59:33Z  
**Author:** v1.1.4

How we accept external files without detonating the UI.

## CSV/TXT
- Delimiter sniffing; header/metadata lines starting with non-numeric tokens are skipped.
- First numeric columns mapped to X and Y; unit detection from header tokens `[nm|Å|um|µm|cm-1]`.
- If unit ambiguous or absent, assume nm and log a warning.

## FITS
- Read using `astropy.io.fits` when available; extract wavelength array or infer from CRVAL/CD/CDELT.
- Honor `WAVEUNIT`/`BUNIT` in headers if present; convert to nm.
- All arrays coerced to float64; NaNs dropped with count logged.

## Dedupe & session scope
- File hashing prevents re-ingest across refreshes when scope is Global.
- Session scope allows re-upload for the current run only.
- "Ingest anyway" override records a provenance note and a warning toast.
