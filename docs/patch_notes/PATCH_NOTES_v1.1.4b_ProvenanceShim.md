# PATCH_NOTES_v1.1.4b — Provenance Shim
Date (UTC): 2025-09-20T00:53:16.498893Z

## Summary
- Add `append_provenance()` **compatibility shim** to `app/utils/provenance.py`.
- Satisfies legacy imports from `app.app_merged` while leaving the v1.1.4 server merger in place.

## Details
- If `app.server.provenance.merge_trace_provenance` is available, the shim delegates to it.
- Otherwise, it performs a minimal local merge into `manifest['traces'][trace_id]['fetch_provenance']`.
- No other behavior is changed.

## Files touched
- `app/utils/provenance.py` (append a guarded shim block)
- `RUN_CMDS/Apply-v1.1.4b-ProvenanceShim.ps1`

## Verification
1. Run the apply script (see Execution Policy note below).
2. Start the app. The import in `app.app_merged` should succeed.
3. Trigger any action that writes provenance; verify the manifest updates.

## Execution Policy
If PowerShell blocks the script as unsigned, run it one of these ways:
```powershell
# Option A: per-process bypass
PowerShell -ExecutionPolicy Bypass -File C:\Code\spectra-app\RUN_CMDS\Apply-v1.1.4b-ProvenanceShim.ps1

# Option B: unblock the file you just extracted
Unblock-File -LiteralPath C:\Code\spectra-app\RUN_CMDS\Apply-v1.1.4b-ProvenanceShim.ps1
# then run:
C:\Code\spectra-app\RUN_CMDS\Apply-v1.1.4b-ProvenanceShim.ps1
```
