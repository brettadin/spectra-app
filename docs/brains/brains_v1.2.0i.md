# Brains — v1.2.0i

## Release focus
- **REF 1.2.0i-A01**: Align the reference trace selector with the Differential workspace so comparison tooling sits together.

## Implementation notes
- Move the reference trace selectbox and clear overlays button into `_render_differential_tab`, reusing a helper that keeps the sidebar examples panel focused on library actions.
- Preserve reference state defaults while filtering overlays, ensuring the overlay plot and similarity tooling continue to pick up the chosen anchor trace.
- Surface the relocation through an AppTest that inspects the differential tab tree for the reference selector and clear action to guard regressions.

## Testing
- `pytest tests/ui/test_differential_form.py`

## Outstanding work
- Consider adding per-tab onboarding to explain how reference traces influence similarity scoring and differential math.
- Revisit the docs index service downtime noted in v1.2.0h once infra availability improves.

## Continuity updates
- Version bumped to v1.2.0i with refreshed patch notes, brains index entry, and AI activity log.
