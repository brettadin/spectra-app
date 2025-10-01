# Brains — v1.2.0f

## Release focus
- **REF 1.2.0f-A01**: Stabilise the example browser provider selector so cached filters survive reruns without triggering Streamlit widget warnings.

## Implementation notes
- Introduced `_normalise_provider_defaults` to compute the multiselect defaults without mutating Streamlit-managed state after widget instantiation.
- The example browser now seeds `st.multiselect` via the helper and defers to `st.session_state.get` for the search box and favourites toggle, matching Streamlit's widget lifecycle.
- Added unit tests that cover stale-provider trimming and fallback behaviour for the helper to guard against regressions.

## Testing
- `pytest tests/ui/test_example_browser.py`

## Outstanding work
- Expand UI smoke coverage once Streamlit snapshot tooling lands so we can assert the widget emits no warnings during reruns.
- Follow up on the duplicated rows in `brains_INDEX.md` for earlier v1.2.0d entries during the next documentation tidy.

## Continuity updates
- Version bumped to v1.2.0f with matching updates to the patch notes (md/txt), patch log, and AI activity log.
