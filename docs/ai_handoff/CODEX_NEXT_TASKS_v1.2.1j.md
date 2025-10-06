# Spectra App – Codex Implementation Targets (v1.2.1j)

This note captures the next wave of high-value implementation tasks for Codex now that the panel registry landed in `v1.2.1i`. Each task references concrete modules/files in the repository and calls out key considerations observed while reviewing the current codebase and the Jdaviz/SpecViz research notes.

## 1. Stabilise the Panel Registry Contract
- **Scope:** `app/ui/panel_registry.py`, `app/ui/main.py`, future panel modules.
- **Deliverables:**
  - Add lightweight unit tests validating duplicate-registration errors, ordering, and `PanelContext` typing to keep regressions from breaking layout assembly.
  - Document registry usage in a module docstring or README snippet explaining sidebar vs. workspace conventions and the required `panel_id` naming scheme.
  - Add a helper to snapshot currently registered IDs for debugging (mirrors Jdaviz’s plugin introspection utilities).
- **Rationale:** Hardens the newly introduced infrastructure and clarifies expectations before extracting more panels.

## 2. Extract Panel Renderers into Dedicated Modules
- **Scope:** `app/ui/main.py` (current inline render functions), potential new folder `app/ui/panels/`.
- **Deliverables:**
  - Move overlay, differential, library, docs, and control render functions into separate modules that register themselves at import time.
  - Provide a shared `build_panel_context()` helper to construct the data passed to renderers, eliminating duplicated session-state lookups and ensuring parity with Jdaviz’s `app.state` usage.
  - Update `main.py` to import the new modules for side effects and to feed context data from a single place.
- **Rationale:** Aligns with the plugin-style pattern we are emulating, making it easier to introduce new analysis panels (e.g., JWST mode explorers) without bloating `main.py`.

## 3. Implement Panel Capability Discovery Hooks
- **Scope:** `app/ui/panel_registry.py`, `app/ui/main.py`, telemetry/logging utilities.
- **Deliverables:**
  - Extend the registry entries to accept optional capability metadata (e.g., supported overlay kinds, required providers, async flags).
  - Surface a debugging/diagnostics tab or sidebar section that lists registered panels and their capabilities to aid QA and plugin authors.
  - Wire capability metadata into session state so downstream features (e.g., disabling controls when no compatible panel is active) become feasible.
- **Rationale:** Mirrors SpecViz configuration-driven UI enabling/disabling and prepares the ground for mode-aware toolsets.

## 4. Roadmap Toward JWST/SpecViz Feature Parity
- **Scope:** `docs/research/specviz_adaptation.md`, ingestion modules under `app/server/`, similarity utilities.
- **Deliverables:**
  - Translate the research blueprint into a tracked checklist mapping SpecViz features (line identification, cube slicing, JWST mode presets) to Spectra App modules.
  - Prioritise implementing JWST spectral mode presets by wiring existing differential math helpers with archive metadata.
  - Define integration tests ensuring new presets still honour overlay downsampling and provenance rules.
- **Rationale:** Keeps momentum toward the adoption goals that triggered the panel registry work and provides incremental milestones for Codex to execute.

## 5. Regression & Documentation Hygiene
- **Scope:** `tests/`, `docs/patch_notes/`, `docs/atlas/brains.md`, `docs/ai_log/`.
- **Deliverables:**
  - Draft regression tests covering the refactored panel import/registration path once panels move out of `main.py`.
  - Continue the established continuity workflow: patch notes, brains entries, AI log updates, and `PATCHLOG.txt` append-only notes for each material change.
  - Capture unresolved questions discovered during implementation (e.g., SIMBAD resolver design choices) in the research notebooks for future follow-up.
- **Rationale:** Prevents drift between code and documentation as the UI architecture evolves.

---

**Suggested sequencing:** Stabilise the registry (Task 1), extract panels (Task 2), augment capabilities (Task 3), then iterate on JWST parity items (Task 4) while keeping regression hygiene (Task 5) in parallel. This ordering keeps the codebase stable while unlocking SpecViz-inspired features.
