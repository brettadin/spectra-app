# Data and Units Specification

Accurate representation of wavelengths and fluxes is fundamental to the integrity of spectral analysis.  The existing Spectra‑App exhibits problems with unit conversions and data mutation (see `reports/bugs_and_issues.md`).  This specification defines canonical internal units, conversion rules and file formats to support precise and reproducible operations.

## 1. Canonical Units

* **Wavelength** – Stored internally in **nanometres (nm)** as a tuple of `float`.  All ingesters convert incoming wavelength values to nm using the conversion factors below.  This canonical array is never mutated.  Derived units are computed on the fly for display.
* **Flux/Intensity** – Stored in an abstract base unit defined by the ingester.  Because different instruments report transmittance, absorbance or absorption coefficients, the canonical flux array is paired with an `IRMeta` structure capturing the original units and scaling factors.  Where possible, the canonical flux is the dimensionless transmittance (0–1) or base‑10 absorbance (A₁₀); the source value is stored in metadata for provenance.

## 2. Wavelength Conversion Rules

Conversions must be idempotent and reversible.  Derived values are computed from the canonical nm array rather than by successive conversions.  The following conversions are supported:

| Target Unit | Formula | Notes |
|---|---|---|
| **Ångström (Å)** | `λ_Å = λ_nm × 10` | 1 nm = 10 Å. |
| **Micrometre (µm)** | `λ_µm = λ_nm ÷ 1000` | 1 µm = 1000 nm. |
| **Wavenumber (cm⁻¹)** | `ν̅ = 10^7 ÷ λ_nm` | Uses the definition of wavenumber (inverse centimetres).  Derived values are floating‑point. |

When converting from wavenumber back to wavelength, use `λ_nm = 10^7 ÷ ν̅`.  Note that converting nm → cm⁻¹ → nm returns exactly the original array if computed in double precision.  All conversions return a new array and leave the canonical nm array unchanged.

## 3. Flux and Intensity Conversions

Flux conversions depend on the measurement type and are defined in `IRMeta`:

| Measurement | Canonical Form | Conversion to A₁₀ | Provenance Fields |
|---|---|---|---|
| **Transmittance (%T or T)** | Fractional transmittance (0–1) | `A₁₀ = -log10(T)`【328409478188748†L22-L24】.  If `%T` is given (0–100), divide by 100 first. | `{'from': 'T', 'percent': True/False}`. |
| **Absorbance (base e)** | Aₑ | `A₁₀ = Aₑ ÷ 2.303`【328409478188748†L28-L32】 | `{'from': 'Ae', 'factor': '1/2.303'}`. |
| **Absorbance (base 10)** | A₁₀ | identity【328409478188748†L32-L35】 | `{'from': 'A10'}`. |
| **Absorption coefficient (α)** | α (m⁻¹) | Requires path length `L` (m) and mole fraction `χ`.  For base 10: `A₁₀ = α × χ × L`【328409478188748†L36-L45】.  For base e: `A₁₀ = (α × χ × L) ÷ 2.303`【328409478188748†L48-L59】. | `{'from': 'alpha10' or 'alpha_e', 'path_m': L, 'mole_fraction': χ, 'factor': '1/2.303' (optional)}`. |

Unknown or unsupported flux units raise an exception rather than attempting a guess.  The ingest UI must prompt users to specify the unit if not encoded in the file header.

## 4. File Formats and Metadata

The application must support importing and exporting spectra in multiple formats:

| Format | Description | Support Notes |
|---|---|---|
| **CSV/TXT** | Tabular text files with columns for wavelength and intensity.  Header lines may include metadata (e.g. instrument, date). | Ingesters should infer column roles by matching keywords (e.g. `lambda`, `wavelength`, `intensity`, `flux`).  Users can override the mapping in the UI. |
| **JCAMP‑DX** | Standardised text format for IR spectra with metadata directives. | Use a JCAMP parser that extracts the `XFACTOR`, `YFACTOR`, `FIRSTX`, `LASTX`, `NPOINTS` and data blocks.  Supports units encoded in headers. |
| **FITS** | Flexible Image Transport System; widely used in astronomy.  Contains binary tables or images. | Use `astropy.io.fits` to read spectra.  Map wavelength and flux columns via header keywords (e.g. `WAVELENGTH`, `FLUX`) and record instrument keywords. |
| **HDF5 / netCDF** | Hierarchical binary formats for large datasets. | Provide optional support via plugins.  Users must select the dataset and variables to ingest. |
| **JSON Manifest** | Structured format produced by the app’s export wizard, capturing data and provenance. | See provenance spec.  JSON manifests can be re‑ingested to restore derived spectra. |

In all cases, ingesters must capture as much metadata as possible: instrument name, spectral resolution, acquisition date and time (in UTC), units, path length, sample composition, and any calibration details.  These fields populate the `metadata` dictionary of the `Spectrum` object.

## 5. Rounding and Precision

All wavelength and flux values are stored as double‑precision floats (IEEE 754).  Display formatting (e.g. number of decimal places) is handled in the UI.  When exporting to text formats, maintain full precision unless the user explicitly requests rounding.

## 6. Unit Tests

Unit tests should verify:

* Round‑trip conversions: nm → µm → nm returns the original array; nm → cm⁻¹ → nm returns the original array; transmittance → A₁₀ → transmittance returns the original fractional values within machine epsilon.
* Appropriate exceptions are raised for unsupported units or missing parameters (e.g. missing path length for α conversions).
* Conversions do not mutate the original arrays.

These tests are provided in the `tests/test_units.py` file.