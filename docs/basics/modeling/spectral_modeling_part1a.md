# Spectral Modeling Part 1a



Spectral Modeling Codes (Part 1.a)



------------------------------------------------------------

PHOENIX

------------------------------------------------------------

\- Stellar atmosphere modeling code.

\- Solves radiative transfer for stars across a wide range of parameters.

\- Inputs: Effective temperature, surface gravity, metallicity, elemental abundances.

\- Outputs: Synthetic stellar spectra for stars, brown dwarfs, supernovae.

\- Handles LTE (local thermodynamic equilibrium) and non-LTE conditions.

\- Practical use: Predicts spectra of stars with varying metallicity, temperature, or structure.



------------------------------------------------------------

Cloudy

------------------------------------------------------------

\- Plasma simulation code, focused on ionized gases (nebulae, AGN, H II regions).

\- Models ionization, recombination, collisional excitation, radiative transfer.

\- Inputs: Incident radiation field, gas density, composition, geometry.

\- Outputs: Emission/absorption lines, continuum spectrum, ionization structure.

\- Widely used for interpreting nebulae, planetary nebulae, quasar environments.

\- Practical use: Compare simulated emission lines to observed nebular spectra.



------------------------------------------------------------

PSG (Planetary Spectrum Generator)

------------------------------------------------------------

\- NASA web-based tool for planetary and exoplanet spectra.

\- Uses radiative transfer and molecular line databases (HITRAN, ExoMol).

\- Inputs: Stellar spectrum, planetary atmosphere composition, pressure/temperature profile, instrument specs.

\- Outputs: Transmission, emission, reflectance spectra at chosen resolution, with simulated noise.

\- Strengths: Tailored for exoplanet studies and mission planning (JWST, Roman, ARIEL).

\- Practical use: Predicts what telescopes would see if a planet with given atmosphere orbited a star.



------------------------------------------------------------

Why These Matter

------------------------------------------------------------

\- PHOENIX → Build a star’s spectrum.

\- Cloudy → Model how its light interacts with gas clouds.

\- PSG → Simulate how planets illuminated by that star appear at multiple wavelengths.



Together these tools allow construction of complete models of star–nebula–planet systems,

and predictions of the resulting spectra. Comparison with observations validates or challenges our physics.



