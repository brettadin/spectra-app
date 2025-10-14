# FTIR overlay readability — 2025-11-03
- Shrunk IR correlation bands, carried probability through each overlay range, and tinted fills according to classifier confidence so the FTIR plot emphasises likely features without overwhelming colour. 【F:app/ui/ir_group_overlays.py†L24-L118】
- Limited overlay annotations to the most confident hits with rotated labels to avoid overlapping titles. 【F:app/ui/ir_group_overlays.py†L118-L143】
- Collapsed the functional-group predictions table behind an expander and refreshed release collateral for v1.2.3. 【F:app/ui/main.py†L3606-L3614】【F:app/version.json†L1-L5】【F:docs/patch_notes/v1.2.3.md†L1-L11】
