**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 04 - API CONTRACTS & UI BINDING (Deep)
Documenting every function the UI expects from the server layer and how to call them safely.

## Fetch router: `app/server/fetch_archives.py`
`fetch(source: str, target: str, **kwargs) -> (spectrum or None, prov)`
- `source` maps to fetcher modules (case-insensitive).
- Validate source before import to avoid injection.
- If unknown source -> return `None, {'error':'unknown_source','source':source}`.

## Model helpers (exposed API)
- `to_spectrum(payload: dict) -> Spectrum` - validate and convert payload to canonical Spectrum dataclass.
- `spectrum_serializable(spec: Spectrum) -> dict` - returns JSON-safe dict for UI export.

## Provenance API (server)
- `merge_trace_provenance(manifest, trace_id, prov)` as described in provenance file.

## UI usage pattern (safe)
```python
# inside a Streamlit handler (button click)
payload, prov = server_fetch.fetch('MAST', target='Vega')
trace_id = make_trace_id()
st.session_state['manifest'] = write_provenance(st.session_state.get('manifest',{}), trace_id, prov)
if payload:
    spec = to_spectrum(payload)
    add_overlay(spec, trace_id)   # UI function that updates TraceSet
else:
    st.warning('Fetch failed: ' + prov.get('message', prov.get('error','unknown')))
```

## Security considerations
- Sanitize `target` and other inputs before sending to external APIs to avoid weird shell injection or query string abuse.
- Rate-limit UI-triggered fetches (disable fetch button while running).
