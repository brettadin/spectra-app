# STATE_KEYS_REFERENCE (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:59:33Z  
**Author:** v1.1.4

Authoritative list of `st.session_state` keys we mutate/read.

```text
axis_unit              -> 'nm'|'Å'|'µm'|'cm⁻¹'
overlays               -> list[OverlayMeta]
docs_selected_path     -> str|None
examples_selected_id   -> str|None
dedupe_scope           -> 'Global'|'Session only'|'Off'
last_error             -> str|None
manifest               -> dict  # provenance manifest
```

Each mutation must be accompanied by a re-render or an inline message, never a silent failure.
