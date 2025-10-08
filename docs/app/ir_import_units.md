# IR import and unit normalization

- JCAMP ingestion multiplies raw Y samples by the declared `YFACTOR`, computes decadic absorbance via `to_A10`, and records conversion provenance or pending parameter requirements for absorption coefficients that need path length and mole fraction inputs.【F:app/server/ingest_jcamp.py†L357-L523】【F:app/server/ir_units.py†L7-L60】
- The parser stores IR sanity diagnostics (YUNITS, YFACTOR, FIRSTX/LASTX, DELTAX, inferred step, and the first scaled samples) alongside the original coefficients so the UI, manifest exporter, and provenance drawer share consistent details.【F:app/server/ingest_jcamp.py†L370-L571】【F:app/export_manifest.py†L23-L62】
- Overlay tooling exposes Streamlit prompts for path length and mole fraction, applies the conversion in-session when supplied, updates provenance/metadata, and rebuilds downsample tiers so traces switch cleanly to A10.【F:app/ui/main.py†L279-L377】【F:app/ui/main.py†L388-L467】
- The workspace plotter infers when cm⁻¹ axes should run high→low, switches to scientific tick/hover formatting, and keeps hover readouts in exponential notation to avoid SI-prefix glyphs.【F:app/ui/main.py†L2452-L2687】
