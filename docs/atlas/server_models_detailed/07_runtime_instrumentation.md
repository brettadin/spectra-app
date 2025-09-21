**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 07 - RUNTIME INSTRUMENTATION & LOGGING (Server)
Where to log, what to log, and how to keep logs useful for debugging UI blanks.

## Logging rules
- Avoid logging during import; initialize logger lazily inside functions.
- Use structured JSON logs written to `logs/server.log` with keys: timestamp, level, module, func, msg, meta.
- For provenance merges, log debug with `trace_id` and `keys` merged.

## UI debug bridge
- `app_patched.py` maintains `logs/ui_debug.log` which records boot timestamps, SmartEntry activity, entrypoints tried, and high-level import success.
- Server-level logs should append to `logs/server.log` and include correlation id (`trace_id` or request id).

## Example log line (JSON)
{
  "ts": "2025-09-20T00:12:00Z", "level":"INFO", "module":"app.server.provenance", "func":"merge_trace_provenance", "trace_id":"abc123", "msg":"merged keys","merged":["fetched_at","source"]
}
