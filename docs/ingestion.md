# Ingestion \& Provenance



\# Spectroscopy Integration Prompt (Implementation Guide)



\## Role

You are an engineer tasked with implementing a robust ingestion, normalization, stitching, and visualization pipeline for heterogeneous spectroscopy data spanning UV → VIS → IR → FIR → sub‑mm → Radio → X‑ray. The system must also support side‑by‑side comparison and overlay of absorption and emission data without misrepresenting physical quantities.



\## Objectives

1\) Ingest heterogeneous spectral files and metadata from multiple instruments and archives.

2\) Normalize all inputs to a canonical internal representation.

3\) Harmonize spectral resolution and rebin to a shared grid using flux‑conserving methods.

4\) Stitch segments across bands with robust overlap scaling.

5\) Provide multiple, physics‑honest display modes for absorption and emission together.

6\) Export the on‑screen view plus a complete provenance manifest.

7\) Preserve an option to view each dataset in its original units while keeping axes and legends unambiguous.



\## Canonical Internals

\- \*\*Spectral axis (internal):\*\* vacuum wavelength in meters (m).

\- \*\*Flux convention (internal):\*\* F\_lambda (e.g., W m^-2 m^-1 or erg s^-1 cm^-2 Å^-1; pick one and keep consistent).

\- \*\*Time/velocity frames:\*\* support barycentric corrections; record the applied frame in metadata.

\- \*\*Error handling:\*\* carry 1σ uncertainties and quality masks through every transform.



\## Ingestion

\- Parse axis type and units: wavelength λ, frequency ν, or wavenumber σ.

\- Parse y‑axis units: F\_lambda, F\_nu, counts, magnitude/absorbance, radiance, brightness temperature.

\- Parse resolution proxies: R=λ/Δλ, slit width, resolving element FWHM.

\- Detect air vs vacuum wavelengths; convert air→vacuum using standard formulae.

\- Apply known wavelength frame corrections if headers specify (e.g., heliocentric/barycentric).



\## Unit Conversions (never silent on the same axis)

\- Convert axes to \*\*vacuum λ (m)\*\*.

\- Convert fluxes to \*\*F\_lambda\*\* where needed:

&nbsp; - F\_nu ↔ F\_lambda via F\_nu = (λ^2/c) F\_lambda.

&nbsp; - Brightness temperature, radiance, or counts require explicit calibration steps; if not available, label as “counts (uncalibrated).”

\- Record every conversion in the provenance manifest.



\## Quality Control

\- Drop NaNs and flag invalid regions from QA masks.

\- Mask known nuisances: order edges, chip gaps, saturation flags.

\- For ground‑based data, mark strong telluric bands (O2 A/B, H2O, CO2).



\## Resolution Harmonization

\- Infer native resolving power R\_native.

\- Choose user‑controlled target R\_display per plot domain; \*\*never up‑resolve\*\*.

\- Convolve higher‑R spectra down to R\_display using an LSF (Gaussian unless instrument LSF known). Record kernel FWHM and method.



\## Flux‑Conserving Rebinning

\- Construct a shared \*\*log‑λ grid\*\* covering the union of all inputs for the current view.

\- Rebin via integration to conserve flux; propagate uncertainties accordingly.

\- Keep band‑aware presets for step sizing tied to target R\_display.



\## Overlap Stitching

\- For adjacent segments with overlap, compute a multiplicative scale in an overlap window:

&nbsp; - Mask edges, telluric regions, and strong emission spikes.

&nbsp; - Use robust statistics (median ratio with σ‑clipping).

\- Apply the scale to the source segment and \*\*record\*\*: segment IDs, overlap bounds, scale value, N used, MAD.

\- Do not alter spectral shapes during scaling.



\## Band‑Specific Notes

\- \*\*FUV (90–200 nm):\*\* vacuum only; watch airglow (Ly‑α). Scale to NUV at 180–200 nm.

\- \*\*NUV (200–400 nm):\*\* some catalogs tabulate in air near 300–400 nm; convert; overlap with VIS at 380–400 nm.

\- \*\*VIS (380–780 nm):\*\* convert air→vacuum; mask O2 A (760.5 nm), B (687 nm), H2O bands.

\- \*\*NIR (0.78–2.5 μm):\*\* heavy tellurics; overlap with VIS at 0.78–0.82 μm and with MIR at 2.3–2.6 μm.

\- \*\*MIR (2.5–28 μm):\*\* many archives provide F\_nu; convert carefully; features at 3.3 μm PAH, 10 μm silicate.

\- \*\*FIR (28–350 μm):\*\* backgrounds important; often in F\_nu; document additive vs multiplicative corrections.

\- \*\*Sub‑mm / mm (0.35–3 mm):\*\* frequency/GHz often natural for display; beam sizes matter.

\- \*\*Radio (>3 mm):\*\* native units often Jy; allow Jy display toggle.

\- \*\*X‑ray/EUV (0.1–100 nm, 0.1–10 keV):\*\* native energy units; provide dual axes (keV and λ); response functions complicate flux conversions—label clearly when transformed.



\## Absorption + Emission Display Modes (non‑destructive)

Provide all four modes; default to Residuals for mixed datasets:

1\. \*\*Twin‑axis overlay:\*\* shared λ; left y = transmission/absorbance/normalized flux; right y = emission flux or counts. Loud labels.

2\. \*\*Residuals (single axis):\*\*

&nbsp;  - Absorption depth: d(λ) = 1 − T(λ) = 1 − I/I0.

&nbsp;  - Emission excess: e(λ) = (I − Ic)/Ic.

3\. \*\*Area‑normalized line profiles:\*\* continuum‑subtract per‑line, normalize to unit area to compare shapes only.

4\. \*\*Small multiples:\*\* vertically stacked panels with linked x‑axis.



Rules:

\- Always share \*\*vacuum λ\*\* and apply barycentric correction consistently.

\- Match \*\*R\_display\*\* across traces.

\- Never place F\_lambda and F\_nu on the same y‑axis; use residuals or twin axes instead.

\- Provide an optional velocity shift tool for small alignment corrections; record applied shift.



\## UI Requirements

\- Band toggles (FUV, NUV, VIS, NIR, MIR, FIR, Sub‑mm, Radio, X‑ray).

\- Unit pill: “Vac λ / F\_lambda” with toggles to “Vac λ / F\_nu,” “Energy (keV),” or “Wavenumber (cm^-1)” depending on band.

\- Resolution slider: presets per band (e.g., UV/VIS/NIR R=3000–10000; MIR/FIR R=600–1500; Radio/X‑ray band‑appropriate).

\- “Jump to features” buttons (Balmer, Paschen, CO bandheads, 10 μm silicate, etc.).

\- Error ribbons and shaded masks for QA/tellurics; hover tooltips show λ (vac), band, R, value, and line ID.

\- Export button: saves PNG + CSV + JSON manifest capturing all transforms.



\## Export / Provenance Manifest (JSON)

Include at minimum:

\- Files and DOIs/URLs; instrument/mode; observation date/time; native axis/units.

\- Axis/flux conversions applied (formulas and constants), air→vac conversion method, barycentric correction.

\- Native R and target R\_display; convolution kernel parameters.

\- Rebin grid definition (bounds, log‑λ step policy).

\- Overlap scaling windows and statistics (median, MAD, N used).

\- Masks applied (tellurics, chip gaps, QA flags).

\- Final display units and any photometric zeropoints used.



\## Minimal Pseudocode (framework‑agnostic)

for spec in spectra:

&nbsp;   x, y, u, meta = load(spec)

&nbsp;   x\_vac = to\_vacuum\_wavelength\_m(x, meta)

&nbsp;   y\_flambda, u = to\_F\_lambda(y, u, meta, x\_vac)   # if already F\_lambda, pass through

&nbsp;   R\_native = infer\_resolution(meta, x\_vac, y\_flambda)

&nbsp;   if R\_native > R\_display:

&nbsp;       y\_flambda, u = convolve\_to\_R(y\_flambda, u, x\_vac, R\_display, lsf=meta.lsf or 'gaussian')

&nbsp;   add\_to\_list((x\_vac, y\_flambda, u, meta))



grid = build\_log\_lambda\_grid(min\_x(all), max\_x(all), R\_display)

rebinned = \[flux\_conserving\_rebin(x,y,u,grid) for (x,y,u,\_) in list]



stitched = \[]

for seg in order\_by\_lambda(rebinned):

&nbsp;   if not stitched:

&nbsp;       stitched.append(seg)

&nbsp;   else:

&nbsp;       scale = robust\_overlap\_scale(stitched\[-1], seg, masks=telluric\_masks)

&nbsp;       stitched.append(apply\_scale(seg, scale))



render(stitched, modes=\['twin','residuals','area','panes'], axes=λ, units='F\_lambda', errors=True, masks=True)

export(stitched, manifest=all\_transforms\_scales\_masks\_metadata)



\## Constraints

\- Do not up‑resolve.

\- Do not mix F\_lambda and F\_nu on the same axis.

\- Do not silently change units.

\- Always log transformations and user choices.



\## Acceptance Criteria

\- Overlays across UV→IR→Radio are visually coherent with correctly labeled axes and matched resolution.

\- Absorption and emission can be compared in any of the four modes without unit confusion.

\- Exports reproduce the on‑screen view exactly and include a complete, machine‑readable manifest.



