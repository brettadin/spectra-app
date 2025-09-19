# Spectroscopy Math Part 2



\# Spectroscopy Math Pack — Part 2 of 2

Deeper physics, tighter math, and the “why” behind the squiggles. Keep this with Part 1.



------------------------------------------------------------

1\) Why spectral lines exist (quantum view)

------------------------------------------------------------

Light couples to matter through the electric-dipole interaction H' = - d · E.

A transition i → j is “allowed” when the transition dipole ⟨j| d |i⟩ ≠ 0.



Atomic electric-dipole (E1) selection rules (non-relativistic):

\- Δl = ±1

\- Δm = 0, ±1

\- Parity must change

\- With total angular momentum J: ΔJ = 0, ±1 but NOT 0 ↔ 0

Weaker multipoles (M1, E2) relax these a bit but have much smaller probabilities.



Molecular selection rules (diatomics, E1):

\- Rotational: ΔJ = ±1 (pure rotation in microwave)

\- Rovibrational: ΔJ = ±1 with branches: P (ΔJ = -1), R (ΔJ = +1), and sometimes Q (ΔJ = 0) in some electronic transitions or for certain symmetries.

\- Vibrational (harmonic): Δv = ±1; overtones (|Δv| > 1) appear by anharmonicity (much weaker).

\- Parity/symmetry and spin statistics further filter lines (Hönl–London factors weight line strengths).



Franck–Condon principle (electronic bands):

\- Electronic transitions are “vertical” in (R, E) space; intensity scales with the overlap of vibrational wavefunctions (Franck–Condon factors).



------------------------------------------------------------

2\) Level populations: Boltzmann and Saha

------------------------------------------------------------

Boltzmann distribution within the same ionization stage:

n\_i / n = (g\_i / Z) exp(-E\_i / kT), with partition function Z = Σ g\_i exp(-E\_i / kT).



Ionization balance (Saha equation):

(n\_{r+1} n\_e) / n\_r = (2 U\_{r+1}/U\_r) (2π m\_e kT / h^2)^{3/2} exp(-χ\_r / kT),

where r indexes ionization stage, U are partition functions, χ\_r ionization energy.



These set the \*available\* atoms/molecules in each state, hence which lines are strong.



------------------------------------------------------------

3\) Einstein coefficients, oscillator strengths, opacity/emissivity

------------------------------------------------------------

Einstein relations (thermal radiation field):

A\_ji = (2 h ν^3 / c^2) B\_ji,   and   g\_i B\_ij = g\_j B\_ji.



Oscillator strength f\_ij links to A\_ji:

A\_ji = (8 π^2 e^2 ν^2 / (m\_e c^3)) (g\_i / g\_j) f\_ij.



Line profile φ(ν) is normalized: ∫ φ(ν) dν = 1.



Absorption coefficient (including stimulated emission):

κ\_ν = (π e^2 / (m\_e c)) f\_{lu} n\_l φ(ν) \[1 - (n\_u g\_l)/(n\_l g\_u)].



Emission coefficient:

j\_ν = (h ν / 4π) n\_u A\_{ul} φ(ν).



In LTE with Boltzmann populations, the bracket term enforces detailed balance so κ\_ν and j\_ν reproduce a Planckian source function.



------------------------------------------------------------

4\) Line shapes and broadening (Voigt)

------------------------------------------------------------

Gaussian (thermal + microturbulent) with Doppler width Δν\_D = (ν\_0 / c) b, where

b = sqrt(2 kT / m + ξ^2),  ξ = microturbulent speed.



Lorentzian (damping) with HWHM γ/4π from natural + collisional (pressure/Stark/van der Waals).



Voigt profile: φ(ν) = (1 / (Δν\_D √π)) H(a, u),

with u = (ν - ν\_0)/Δν\_D and a = γ / (4π Δν\_D). H is the Hjerting/Voigt function.



Physical origins:

\- Natural: finite upper-level lifetime (ΔE Δt ≈ ħ/2).

\- Doppler: thermal motions randomize velocities.

\- Collisional: perturbations of energy levels during encounters (density dependent).

\- Stark: electric fields split/broaden lines (ionized environments).

\- Zeeman: magnetic fields split components (see below).



------------------------------------------------------------

5\) Equivalent width and the curve of growth

------------------------------------------------------------

Equivalent width: W\_λ = ∫ (1 - I\_λ / I\_c) dλ.

Basic regimes vs column density N (and f-value):

\- Linear (optically thin): W\_λ ∝ N f.

\- Saturation: line core blackens; W\_λ grows slowly (∝ √ln(N f)).

\- Damping wings: W\_λ ∝ (N f)^{1/2} as Lorentz wings dominate.



Curve-of-growth analysis disentangles N, b (Doppler), and γ (damping) from measured W\_λ values across multiple lines.



------------------------------------------------------------

6\) Continuum processes (why there’s a baseline)

------------------------------------------------------------

\- Bound–free (photoionization): κ\_ν rises toward edges; edges imprint discontinuities (e.g., Balmer jump).

\- Free–free (Bremsstrahlung): j\_ν ∝ n\_e n\_i Z^2 g\_ff T^{-1/2} exp(-hν/kT) (radio–IR–mm continua).

\- Scattering: Rayleigh ∝ λ^{-4}; Thomson (electron) is gray; Mie for dust gives complex wavelength dependence.



Continuum sets I\_c that your lines sit on; mis-modeled continuum wrecks abundance estimates.



------------------------------------------------------------

7\) Magnetic fields: Zeeman and polarization

------------------------------------------------------------

Zeeman splitting:

ΔE = μ\_B g\_J m\_J B,   ⇒   Δλ ≈ (e λ^2 B / (4 π m\_e c^2)) g\_eff.

Patterns (π, σ± components) carry linear/circular polarization signatures.



Stokes vectors S = (I, Q, U, V) evolve via the polarized transfer equation

dS/ds = -K S + ε, with propagation matrix K encoding dichroism and dispersion.



------------------------------------------------------------

8\) Radiative transfer: formation of a line

------------------------------------------------------------

Scalar transfer: dI\_ν/dτ\_ν = I\_ν - S\_ν, with τ\_ν = ∫ κ\_ν ρ ds.

Formal solution along a ray (toward the observer):

I\_ν(0) = I\_ν(τ) e^{-τ} + ∫\_0^τ S\_ν(t) e^{-(t)} dt.



Eddington–Barbier insight (plane-parallel, LTE): emergent intensity at μ ≈ S\_ν evaluated at τ\_ν ≈ μ.

Line cores form higher (larger τ at ν\_0); wings form deeper. That vertical stratification encodes T, v, n\_e with frequency.



Non‑LTE: level populations are set by statistical equilibrium

Σ\_j n\_j P\_{j→i} = n\_i Σ\_k P\_{i→k},

with radiative (A,B) and collisional (C) rates. Critical density n\_crit ≈ A\_ul / q\_ul divides LTE-like (collisions dominate) from non-LTE.



------------------------------------------------------------

9\) Molecular spectroscopy specifics

------------------------------------------------------------

Rotational (rigid rotor): E\_J = B J(J+1), spacing ~ 2B (in wavenumber). Selection ΔJ = ±1.

Vibrational (anharmonic oscillator): E\_v ≈ ω\_e (v+1/2) - ω\_e x\_e (v+1/2)^2.

Rovibrational bands (IR): P (ΔJ = -1), R (ΔJ = +1); Q often absent for Σ–Σ but present for some symmetries (e.g., Π–Π).

Electronic bands (UV/vis): term symbols (e.g., ^2Π\_3/2), spin–orbit splittings, and vibronic structure with Franck–Condon envelopes.

Line strengths weighted by Hönl–London factors and Boltzmann populations; hot bands arise from thermally populated v>0.



Partition functions: Z\_mol(T) factor into rotational × vibrational × electronic (approximately), each with its own T-scaling.



------------------------------------------------------------

10\) Instrumental physics (what the hardware does to spectra)

------------------------------------------------------------

Grating equation: m λ = d (sin α + sin β); blaze angle optimizes efficiency.

Resolving power: R = λ/Δλ ≈ m N (order × illuminated grooves). Instrumental profile typically near-Gaussian; convolve with physics line.

Sampling: ≥ 2 pixels per resolution element (Nyquist) but ~3 is healthier.

Throughput/étendue: governs SNR with given aperture and slit; slit losses broaden the LSF.

Echelle spectrographs: high m with cross‑disperser to separate orders; “blaze function” imprints order‑dependent continuum.



------------------------------------------------------------

11\) Signal‑to‑noise and exposure math (CCD/CMOS)

------------------------------------------------------------

Source counts N\_s = F\_λ A\_tel η t (per resel), background N\_b per pixel; dark N\_d; read noise RN.

SNR ≈ N\_s / sqrt(N\_s + n\_pix (N\_b + N\_d + RN^2)).

Binning and longer t raise SNR until systematics dominate.

Radial‑velocity precision (photon limit): σ\_v ≈ c / (Q √N\_ph), where Q encodes line density, depth, and resolution.



Cross‑correlation RVs: compute CCF with a binary mask or template, fit peak for shift; apply barycentric correction to tie to solar system rest frame.



------------------------------------------------------------

12\) Abundances from lines

------------------------------------------------------------

Measure equivalent widths or fit full profiles.

Forward model: choose T–P structure, micro/macro‑turbulence, v\_rad, v\_rot, abundances; compute κ\_ν, j\_ν, solve transfer → synthesize spectrum; optimize parameters (χ² or Bayesian).

Microturbulence adjusts the flat part of the curve of growth; macroturbulence and rotation broaden without changing EW much.



------------------------------------------------------------

13\) Continuum placement and tellurics

------------------------------------------------------------

Continuum errors bias W\_λ; use standard stars or models to set I\_c.

Telluric absorption (H2O, O2, CO2) multiplies your spectrum; divide by a telluric model/standard, or fit jointly during retrieval.



------------------------------------------------------------

14\) Retrieval and inversion (why fitting works)

------------------------------------------------------------

We solve an inverse problem: find parameters θ that best reproduce data d given forward model F(θ).

\- Optimal estimation: minimize (d - F(θ))^T S\_n^{-1} (d - F(θ)) + (θ - θ\_a)^T S\_a^{-1} (θ - θ\_a).

\- Bayesian: sample p(θ | d) ∝ p(d | θ) p(θ).

Sensitivity lives in contribution functions (∂I\_ν/∂x). Ill‑posedness needs priors/regularization.



------------------------------------------------------------

15\) Quick numeric forms (handy)

------------------------------------------------------------

Thermal Doppler b \[km/s] ≈ 0.129 √(T/A), A=atomic weight.

Zeeman splitting (approx): Δλ\[Å] ≈ 4.67×10^{-13} g\_eff λ^2\[Å] B\[G].

Wien displacement: λ\_max\[µm] ≈ 2898 / T\[K].

Rydberg for H: 1/λ = R (1/n\_1^2 - 1/n\_2^2), R ≈ 109737 cm⁻¹.



------------------------------------------------------------

16\) Why features look the way they do (short narrative)

------------------------------------------------------------

\- Lines appear because charged particles have quantized energy ladders and light kicks them between rungs when symmetry allows.

\- Depth and shape are a census of who’s in which rung (Boltzmann/Saha), how chaotic the motions are (Doppler/turbulence), how crowded the room is (collisions/pressure), and whether magnetic/electric fields are poking them (Zeeman/Stark).

\- The continuum is your canvas, painted by free‑free, bound‑free, and dust scattering. Get that wrong and every color you measure shifts.

\- Instruments smear reality by an LSF that you must deconvolve or model. Sky and tellurics add their graffiti. Good calibration is the difference between science and modern art.



End of Part 2.



