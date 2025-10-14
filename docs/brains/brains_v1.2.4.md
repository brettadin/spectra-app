# FTIR overlay peak focus — 2025-11-04
- Reworked the shaded range helper to weight classifier bands by measured intensity, clamp spans to observed widths, and blend colours using confidence plus peak fractions for cleaner FTIR visuals.【F:app/ui/ir_group_overlays.py†L1-L198】
- Fed the classifier trigger with the active spectrum vectors so overlay selection can filter to the highest-intensity detections for the reference trace.【F:app/ui/main.py†L3639-L3664】
- Captured regression coverage ensuring the intensity-aware ordering and fallback trimming behave deterministically.【F:tests/ui/test_ir_group_overlays.py†L1-L54】
