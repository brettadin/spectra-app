**Timestamp (UTC):** 2025-09-20T05:09:34Z  
**Author:** v1.1.4c9


# 05 - TESTS, CI & QUALITY (Server)
This file outlines unit tests, integration tests, and CI checks for the server layer.

## Unit tests (suggested)
- `test_models_validation` — invalid arrays, mismatched lengths, NaNs.
- `test_provenance_merge_init` — merge into None manifest creates required keys.
- `test_provenance_merge_idempotent` — repeated identical merges are no-ops.
- `test_fetcher_error_handling` — fetcher returns (None, prov_with_error) on HTTP 500.
- `test_to_spectrum_serialization` — round trip to dict and back.

## Integration tests (CI)
- Use recorded fixtures (VCR) for fetcher network calls.
- Run fetchers against a local mocked server returning canned responses.
- Smoke test: call `fetch_archives.fetch('mast','Vega')` and ensure no exceptions, and prov contains `source` and `fetched_at`.

## Linting & static checks
- `flake8`, `pydocstyle`, `mypy` (if typed) for server modules.
- GitHub Actions workflow: run tests in matrix Python 3.10/3.11; cache pipenv/venv; fail on untested code coverage drop.

## Test fixtures
- Keep a `tests/fixtures/mast_v0.json` and `tests/fixtures/mast_v1.json` for stable parsing behavior.
