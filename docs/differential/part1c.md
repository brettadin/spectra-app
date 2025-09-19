# Differential Tool Part 1c





Differential/Backlit Spectroscopy Playbook (Part 1.c)



0\) Define geometry \& goal

\- Geometry: transit, eclipse/occultation, phase curves, or direct imaging with coronagraph/AO.

\- Target signal: transmission lines, reflected-light features, thermal emission bands.

\- Wavelengths: choose bands with strong target opacities and manageable tellurics.



1\) Precompute expectations (forward models)

\- Inputs: stellar SED, ephemerides, planetary radius/gravity, P–T profile, composition priors.

\- Outputs: trial spectra to pick instrument, resolution, cadence, exposure times, and spectral windows.



2\) Instrument selection \& setup

\- Spectral resolution: low/medium for bands, high (R ≥ 25k) for line-by-line HRCCS.

\- Stability: favor instruments with precise wavelength control and repeatable systematics.

\- Calibrations: wavelength standards (ThAr/etalon/comb), flats, darks, spectrophotometric standards.



3\) Observing strategy

\- Baseline (out-of-event) spectra bracketing in-event data.

\- Transmission: continuous coverage from pre-ingress to post-egress.

\- Emission/eclipse: star+planet before eclipse, star-only during eclipse.

\- Direct imaging: coronagraph/AO with ADI; consider SDI/RDI for PSF subtraction diversity.

\- Record housekeeping: temperature, drift, FWHM, airmass, slit losses.



4\) Raw calibration

\- Bias/dark subtraction, flat-fielding, cosmic-ray removal.

\- Optimal extraction of 1D spectra from 2D frames; track spatial drifts.

\- Wavelength solution from lamps/etalon; refine with sky/tellurics; apply barycentric correction.

\- Flux calibration and blaze correction; build instrument response curves.

\- Telluric correction by standard-star division or line-by-line modeling; mask saturated regions.



5\) Align \& normalize time series

\- Interpolate to a common wavelength grid; cross-correlate to remove small drifts.

\- Continuum normalization per order/channel while preserving line shapes.

\- Build out-of-event template F\_out(λ) via robust averaging.



6\) Construct planetary signal

Transmission (in transit):

\- Ratios: R(t,λ) = F(t,λ) / F\_out(λ). Average in-transit to get T(λ); remove white-light depth.

\- Convert to effective radius/height spectrum; relate to scale height and opacity.

Emission/reflectance (secondary eclipse):

\- Eclipse depth Δ(λ) = \[F\_star+planet − F\_star] / F\_star.

\- Infer brightness temperature or geometric albedo vs. wavelength.

High-resolution HRCCS:

\- Detrend with SYSREM/PCA/GP to suppress stellar/telluric residuals.

\- Cross-correlate Doppler-shifted molecular templates along expected v\_p(t); coadd in planet rest frame.



7\) Systematics removal

\- Regress against auxiliary vectors (airmass, drift, FWHM, background).

\- Low-rank models (PCA/ICA/SYSREM) with caution; preserve planetary signal.

\- Gaussian Processes for time-correlated noise; propagate to uncertainties.



8\) Error analysis \& validation

\- Photon noise propagated from counts.

\- Systematic error from residual scatter and GP fits.

\- Red-noise test: RMS vs. bin size; departures from 1/sqrt(N) indicate correlation.

\- Injection–recovery at pixel level to measure sensitivity and self-subtraction.

\- Repeatability across nights/instruments.



9\) Stellar contamination controls

\- Model unocculted spots/faculae and center-to-limb variation; handle Rossiter–McLaughlin effects.

\- Compare residuals with stellar atmosphere models to separate stellar vs. planetary features.



10\) Retrieval \& inference

\- Forward model F(θ,λ); parameters: abundances, clouds/hazes, P–T profile, radius offset, winds/rotation, reflectance.

\- Opacities from vetted line lists; convolve with instrument LSF.

\- Bayesian inference (MCMC/nested sampling); report posteriors and detection significances.

\- Model selection with Bayes factors/AIC/BIC.



11\) Solar System special case

\- Use reflectance I/F: divide by solar irradiance scaled to heliocentric distance; correct viewing geometry.

\- Fit photometric models (Hapke/Shkuratov) to decouple composition from grain size/texture.

\- Subtract scattered light from nearby bright bodies using IFU data and PSF modeling; on/off-line narrowband differencing for faint emissions.



12\) Quality gates \& deliverables

\- Provide: per-exposure 1D spectra, common-grid time series, transmission/emission spectra with covariance, HRCCS correlation maps, posterior samples.

\- Provenance manifest: calibration frames, extraction settings, telluric model/version, wavelength zero-points, barycentric corrections.

\- Validation plots: white-light \& spectroscopic light curves, detrending diagnostics, injection–recovery curves, residual heatmaps.



13\) Pitfalls \& mitigations

\- Self-subtraction in PCA/SYSREM → quantify with injections; limit components.

\- Template mismatch (HRCCS) → broaden for winds/rotation; explore P–T/abundance grids.

\- Degeneracies (radius offset vs. clouds; temperature vs. composition) → multi-band coverage and informative priors.

\- Telluric residuals → avoid saturated bands; co-model or mask.

\- Stellar heterogeneity → multi-epoch monitoring and heterogeneity-aware modeling.



14\) Minimal working recipes

Transmission:

1\) Reduce/extract; align; build F\_out(λ).

2\) Compute ratios R(t,λ); detrend with regressors/low-rank models; verify with injections.

3\) Average in-transit to T(λ); estimate errors with GP/binned RMS.

4\) Retrieve composition/clouds with instrument-convolved forward model; report posteriors.

HRCCS:

1\) Calibrate/extract; continuum removal.

2\) Remove telluric/stellar lines with SYSREM/PCA while preserving Doppler-shifted signals.

3\) Cross-correlate templates along v\_p(t); coadd in planet rest frame; assess significance by permutation/bootstrap.

4\) Map line contrast vs. phase; retrieve abundances/temperatures/winds.



Summary:

Plan with forward models, secure clean baselines, construct differential spectra with disciplined detrending, validate via injection–recovery, and finish with Bayesian retrieval that respects the instrument and correlated noise.



