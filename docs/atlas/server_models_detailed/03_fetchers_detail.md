**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 03 - FETCHERS (Detailed)
Fetchers are thin adapters that query archives, return a standardized spectrum object and a provenance dict.

## Location
`app/server/fetchers/` with modules: `mast.py`, `simbad.py`, `eso.py` and `__init__.py` exporting metadata.

## Fetcher signature
```python
def fetch(target: str, **kwargs) -> Tuple[Optional[dict], dict]:
    # returns (spectrum_payload, provenance_payload)
```
- `spectrum_payload` minimal accepted form: `{'wavelength_nm': [...], 'flux': [...], 'meta': {...}}` or `None` on failure.
- `provenance_payload` must be a dict as described in PROVENANCE_PAYLOADS.

## Error & retry policy
- Use `requests` with `timeout=(3.05, 10)` and limited retries (3) using `urllib3.util.retry` or `requests` adapters.
- On HTTP 429 or 5xx, implement exponential backoff with capped retries.
- Do not raise inside fetcher; return `None` and a provenance payload with `error` keys, e.g., `{'error':'http_500','status':500,'message':'...'}`.

## Example for MAST (pseudo)
```python
def fetch(target):
    prov = {'source':'MAST','query':{'target':target}, 'fetched_at':now()}
    try:
        # use requests or astroquery here
        res = call_api(...)
        data = parse_res(res)
        prov.update({'ids': data.get('ids'), 'url':res.url})
        payload = {'wavelength_nm': data['wavelength_nm'], 'flux': data['flux'], 'meta': data.get('meta',{})}
        return payload, prov
    except Exception as e:
        prov.update({'error':'fetch_error','message':str(e)})
        return None, prov
```

## Testing fetchers
- Unit tests can simulate HTTP responses with `responses` or `httpx` mocking.
- Validate payload shape and provenance keys.
