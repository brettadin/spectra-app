# 04_ERROR_HANDLING_CONTRACT (v1.1.4x)

**Rule:** no silent failures; no page wipes.

## UI errors
- Wrap panel handlers in try/except.
- Render `st.error(f"{context}: {exc}")` and continue showing the frame.
- Log: `HANDLER_ERR <panel> <action> <exception>`.

## Loader/entry errors
- If entry lookup fails, render a minimal page with a red banner and display available exports.

## Data ingest errors
- On parse/unit failures, render inline error and attach provenance of the source path.
