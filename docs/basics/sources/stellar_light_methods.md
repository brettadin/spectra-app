# Stellar Light Methods



You want \*every\* way humans look at light from stars and planets and how folks store that stuff in databases. Fine. I did the boring legwork so you don’t have to. Below: a compact catalog — name + one-line description — with authoritative docs so you can follow the breadcrumbs. If you want, I’ll expand any entry into formats, example FITS headers, DB schemas, or ingestion scripts. But right now: names and a sentence each, with sources. Enjoy your tidy little pile of astrophysical chaos.



\# Ways / tools to observe light (name — one-line description + doc)

1\. \*\*Imaging (CCD / CMOS photometry)\*\* — direct imaging using CCD/CMOS detectors to measure brightness and morphology (broadband and narrowband). \[Doc](https://www.aanda.org/articles/aa/full\_html/2018/11/aa32588-18/aa32588-18.html)

2\. \*\*Broadband / Narrowband Photometry\*\* — measuring flux through filters (e.g., UBVRI, SDSS) to get colors and rough SEDs; the basic input for light curves and catalogs. \[Doc](https://ui.adsabs.harvard.edu/abs/2002AJ....123..485S/abstract)

3\. \*\*Transit Photometry (space: Kepler, TESS)\*\* — high-precision time series (light curves) that record dips when planets transit their stars; typically stored as FITS light-curve products. \[Kepler](https://archive.stsci.edu/kepler/) \[TESS](https://archive.stsci.edu/tess/)

4\. \*\*Radial-velocity (Doppler) spectroscopy (HARPS, HIRES, etc.)\*\* — high-resolution spectra used to measure line shifts and infer planet masses via Doppler wobble. \[HARPS](https://www.eso.org/sci/facilities/lasilla/instruments/harps/overview.html)

5\. \*\*Slit / Echelle Spectroscopy (HIRES, HARPS, HIRES docs)\*\* — dispersing light to high spectral resolution for line IDs, abundances, velocities, stored as calibrated 1D/2D spectra (often FITS). \[HIRES](https://www2.keck.hawaii.edu/inst/hires/)

6\. \*\*Integral Field Spectroscopy (MUSE, IFUs)\*\* — 3D data cubes (x, y, λ) that give spatially resolved spectra across a field; outputs are cube FITS files and pipeline products. \[MUSE](https://www.eso.org/sci/facilities/paranal/instruments/muse.html)

7\. \*\*Multi-Object Spectroscopy (MOS, e.g., NIRSpec MOS)\*\* — simultaneous spectroscopy of many targets via slitmasks or microshutters for survey efficiency (data packaged per-object/file). \[JWST NIRSpec](https://jwst-docs.stsci.edu/jwst-near-infrared-spectrograph)

8\. \*\*Integral-field / IFU time-series\*\* — IFU spectroscopy used for time-series work (exoplanet atmospheres, stellar variability). \[JWST IFU](https://jwst-docs.stsci.edu/)

9\. \*\*Fourier-Transform Spectroscopy (FTS)\*\* — interferometer-based spectroscopy yielding very accurate spectral profiles used in lab and some astronomical contexts; outputs are spectral scans. \[NIST FTS](https://www.nist.gov/pml/atomic-spectra-database)

10\. \*\*High-contrast Direct Imaging (coronagraphy, SPHERE, coronagraph-equipped telescopes)\*\* — block stellar light to image faint planets/disks; data include raw frames, coronagraphic reductions, and contrast curves. \[SPHERE](https://www.eso.org/sci/facilities/paranal/instruments/sphere/)

11\. \*\*Adaptive Optics (AO) imaging\*\* — ground telescopes using AO to correct atmosphere and approach diffraction limit for high-resolution imaging used with coronagraphs and imagers. \[ESO AO](https://www.eso.org/sci/facilities/develop/instruments/adaptiveoptics.html)

12\. \*\*Interferometry (VLTI, long-baseline)\*\* — combine light from multiple telescopes to achieve extremely high angular resolution (visibilities, closure phases); outputs are interferometric observables and calibrated products. \[VLTI](https://www.eso.org/sci/facilities/paranal/telescopes/vlti.html)

13\. \*\*Polarimetry / Spectro-polarimetry\*\* — measure polarization (often wavelength dependent) to study scattering, magnetic fields, or dusty disks; stored as polarized flux spectra or images. \[Polarimetry](https://www.aanda.org/articles/aa/full\_html/2018/07/aa32809-18/aa32809-18.html)

14\. \*\*Occultation / Eclipse observations\*\* — timing/photometry when a body passes in front of a star (stellar occultation) to measure sizes, atmospheres, rings — time series \& derived profiles recorded. \[Occultation](https://ui.adsabs.harvard.edu/abs/2010AJ....139.2700Y/abstract)

15\. \*\*Astrometry (Gaia)\*\* — ultra-precise position/time measurements (parallax/proper motion) that indirectly reveal planets by reflex motion; large catalogs with per-source metadata. \[Gaia](https://gea.esac.esa.int/archive/)

16\. \*\*Sub-mm / Radio continuum \& spectral line (ALMA)\*\* — millimeter/submm interferometry captures thermal emission and molecular lines from disks/planetary atmospheres; data products: measurement sets, FITS images, calibrated cubes. \[ALMA](https://almascience.nrao.edu/asax/)

17\. \*\*Infrared photometry / spectroscopy (Spitzer, JWST NIRSpec/MIRI)\*\* — thermal and molecular features in IR; JWST instruments provide calibrated spectra and IFU cubes with extensive documentation. \[JWST](https://jwst-docs.stsci.edu/)

18\. \*\*Time-domain / Survey imaging (ZTF, LSST in future)\*\* — wide-field survey photometry producing catalogs and light-curve databases for variability/transients relevant to stellar activity and exoplanet detection. \[ZTF](https://irsa.ipac.caltech.edu/Missions/ztf.html)

19\. \*\*Laboratory lamp / calibration spectroscopy (NIST, lab FT spectra)\*\* — lab reference spectra used to identify lines and calibrate wavelengths; entered alongside observational data in provenance records. \[NIST ASD](https://www.nist.gov/pml/atomic-spectra-database)

20\. \*\*Detector types \& readouts (CCD, EMCCD, PMT, bolometer, photodiode)\*\* — how photons become numbers: detectors define data characteristics (linear range, noise, QE) and thus database fields (gain, readnoise, exposure). \[CCD basics](https://www.stsci.edu/hst/instrumentation/wfc3/data-analysis/ccd-overview)



\# How others \*record\* these observations (short form)

\- \*\*FITS files + rich headers\*\* — standard archival container for images, spectra, and cubes; stores data arrays and metadata keywords (WCS, units, instrument, exposure, pipeline version). This is the backbone of astronomical archives. \[FITS Standard](https://fits.gsfc.nasa.gov/fits\_standard.html)

\- \*\*Mission/Instrument pipeline products\*\* — e.g., Kepler/TESS light-curve FITS, JWST calibrated spectra/cubes, ESO reduced products; archives publish product definitions \& ingestion rules. \[MAST](https://archive.stsci.edu/missions-and-data) \[ESO](https://www.eso.org/sci/observing/phase3.html)

\- \*\*Database catalogs / tables\*\* — per-object tables with metadata: RA/Dec, time stamps, fluxes, errors, quality flags, provenance IDs (DOI, ingest batch, pipeline version). Examples: Gaia catalogs, Exoplanet Archive, VizieR. \[VizieR](https://vizier.cds.unistra.fr/)

\- \*\*Light-curve/time-series stores\*\* — time, flux, flux\_err, quality flags, cadence info stored as table rows or per-object FITS time series (Kepler/TESS style). \[Kepler Archive](https://archive.stsci.edu/kepler/)

\- \*\*Cube / IFU storage\*\* — 3D FITS (x,y,λ) plus auxiliary files (variance, mask, QA reports), often bundled in tarballs for archive download. \[MUSE data](https://www.eso.org/sci/facilities/paranal/instruments/muse/tools.html)

\- \*\*Observatory archives \& APIs\*\* — MAST, ESO archive, ALMA archive, Keck archive provide programmatic access (TAP, SIA/SSAP, APIs) and recommended ingest formats. \[MAST APIs](https://mast.stsci.edu/api/v0/)



\# Key archives \& format docs (so you can stop guessing)

\- \*\*FITS standard (nasa.gsfc / IAU)\*\* — canonical FITS spec. \[FITS](https://fits.gsfc.nasa.gov/fits\_standard.html)

\- \*\*MAST (STScI) archive guidelines \& mission docs (HST, JWST, Kepler, TESS)\*\* — product descriptions and data-format guidance. \[MAST](https://archive.stsci.edu/missions-and-data)

\- \*\*ESO instrument manuals \& pipeline docs (MUSE, SPHERE, VLTI, HARPS)\*\* — instrument-level details and data product definitions. \[ESO](https://www.eso.org/sci/facilities/paranal/instruments.html)

\- \*\*HARPS / High-precision RV docs\*\* — examples of how radial-velocity data and calibration are recorded. \[HARPS](https://www.eso.org/sci/facilities/lasilla/instruments/harps/overview.html)

\- \*\*Keck / HIRES docs\*\* — typical high-resolution spectrograph product \& calibration details. \[HIRES](https://www2.keck.hawaii.edu/inst/hires/)

\- \*\*ALMA science archive manual \& notebooks\*\* — how interferometric mm data are packaged and accessed programmatically. \[ALMA](https://almascience.nrao.edu/asax/)

\- \*\*Gaia data release pages\*\* — example of massive astrometric catalogs and their schemas. \[Gaia](https://gea.esac.esa.int/archive/)



