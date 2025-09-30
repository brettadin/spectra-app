It is important for all investigators who publish scientific results based on JWST data to properly acknowledge the mission and (if applicable) the source of funding.  Likewise, for reproducibility, it is critical to state the versions of the calibration pipeline software and reference files used for published analyses.

# Citing the mission

All scientific publications using JWST data obtained from MAST should include standard acknowledgements, the text of which may vary based on the type of data used, and whether a NASA grant funded the research program that produced the publication. The text of these acknowledgements can be found on the [MAST Mission Acknowledgements](https://archive.stsci.edu/publishing/mission-acknowledgements) page. Authors are also encouraged to cite one or more papers that describe the instrument design or on-orbit performance, as appropriate.

---

# Citing the data

Citing the data analyzed in a research paper is important for measuring the impact of mission data, and for promoting scientific reproducibility in the literature. MAST provides a utility for researchers to create a digital object identifier (DOI), which is a persistent link to your data in MAST. Recipients of JWST grants are also reminded of their obligation to create DOIs for JWST data they publish. See the [Special Topics](https://outerspace.stsci.edu/display/MASTDOCS/Special+Topics) chapter of the JWST Archive Manual for details of how to create such DOIs, and how to use them to create links from your papers to MAST.

MAST DOIs refer to all stages of JWST processing. Even if you recalibrated the data yourself, a DOI that refers to the latest stage(s) of processing also implicitly points to uncalibrated data products.

---

# Citing the software

There are two software pipelines whose versions should be stated in any publications.

The JWST Science Data Processing (SDP) subsystem is the software that generates the raw data products ("uncal") from the original spacecraft telemetry. This version is captured in the FITS header of all JWST data products using the keyword `SDP_VER`. (e.g., "2022\_3").

The JWST Science Calibration Pipeline is the software that processes data from all instruments and observing modes to generate fully calibrated individual exposures and high level data products (mosaics, extracted spectra, etc.). This version is captured in the FITS header of all JWST data products using the keyword `CAL_VER` (e.g., "1.7.2").

Observers who wish to cite the [JWST Science Calibration Pipeline](/jwst-science-calibration-pipeline) software itself can use the [digital object identifier (DOI) on Zenodo](https://zenodo.org/records/16280965).

Some observers may choose to process their data manually using modified versions of the science calibration pipeline and parameters in the calibration steps. Because changing the default calibration pipeline steps or parameters may produce different results, it is important to share this information in publications by describing (for example) which parameters to change for certain calibration steps, or by pointing to code or Jupyter notebooks stored in a public hosting service for software, such as GitHub. 

---

# Citing the reference files

All reference files used by the science calibration pipeline are stored in the [Calibration Reference Data System (CRDS)](https://jwst-crds.stsci.edu/), and the CRDS context defines the set of rules used to select the best reference files for an instrument and mode. Throughout the life of the mission,  instrument teams will continue to analyze calibration data to update and deliver in-flight reference files. Because the reference files will be periodically updated, publications should include the CRDS context version used for data processing. This version is captured in the FITS header of all JWST data products using the keyword `CRDS_CTX` (e.g., "jwst\_0955.pmap").

For publications using science data reprocessed by individual users prior to November 10, 2022 it is also important to include the name of the CRDS server used as two were initially in use during JWST commissioning and the first few months of Cycle 1 science observations. The secondary "CRDS-PUB" server has since been decommissioned, and all processing is done with the "CRDS-OPS" server.

Observers who wish to cite the CRDS software system itself can reference [Greenfield & Miller (2016)](#CitingJWSTData-ref).

---

# References

[Greenfield, P., & Miller, T. 2016, *Astron. Comput.*, 16, 41 (ADS)](https://ui.adsabs.harvard.edu/abs/2016A%26C....16...41G/abstract)  
The Calibration Reference Data System

---

```

```

```

```

---