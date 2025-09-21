# TEST_PLAN_PROVENANCE (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:51:22Z  
**Author:** v1.1.4

### Unit tests (server)
- `merge_trace_provenance` initializes missing structures.
- Merges additional keys without clobbering previous ones.
- Updates `last_updated`.

### Unit tests (utils shim)
- When server merger is present, it forwards calls.
- When missing, it performs minimal in-place update.

### UI smoke tests
- After a fetch, drawer shows non-empty JSON.
- Export JSON button produces a file with valid keys.
