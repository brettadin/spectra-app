# BADGE_SPEC (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:48:19Z  
**Author:** v1.1.4

**Source:** `app/version.json`

```json
{
  "version": "v1.1.4",
  "patch": "c9",
  "timestamp": "2025-09-20T00:00:00Z"
}
```

**Behavior:**
- Read on each run; small JSON means negligible cost.
- If missing, show `v?` and log a warning.
- Do not cache; rely on reruns to refresh.
