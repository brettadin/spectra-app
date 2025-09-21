# TEST_PLAN_UNITS_AND_MODEL (v1.1.4x)
**Timestamp (UTC):** 2025-09-20T04:59:33Z  
**Author:** v1.1.4

### Unit tests
- nm→Å→µm→cm⁻¹→nm round-trip within 1e-9 relative error.
- `convert_x` vectorized behavior matches scalar formulas.
- `Spectrum.slice` honors inclusive bounds and preserves meta/provenance.

### UI smoke
- Toggling units re-renders axes but not data arrays; overlay count unchanged.
- Uploading the same CSV twice with Global scope results in one overlay with a provenance note on dedupe.
- Docs/Examples handlers never blank the page; errors render inside container.
