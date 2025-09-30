The duration of a JWST observation can be described using 3 characteristic time definitions, each with their own purpose: exposure time, measurement time, and saturation time.

The [complex readout patterns](/understanding-exposure-times) of the JWST instrument detectors lead to multiple ways to measure the duration of an observation. Different times are used for different purposes in the [Astronomers Proposal Tool (APT)](/jwst-astronomer-s-proposal-tool-overview) and the [Exposure Time Calculator (ETC)](/jwst-exposure-time-calculator-overview), and the [JWST Science Calibration Pipeline](/jwst-science-calibration-pipeline) reports a variety of different time-related keywords. Users interested in the full equations should read the [JWST technical document by Holler et al. (2021)](#JWSTTimeDefinitions-Refs). See also [Understanding Exposure Times](/understanding-exposure-times) for a basic introduction to JWST up-the-ramp readout.

---

# Time definitions

Words in **bold** are GUI menus/  
panels or data software packages;   
***bold italics***are buttons in GUI  
tools or package parameters.

The different times can be divided into 2 broad categories:

* Pixel-based time: Time with respect to a single pixel.
* Array-based time: Time with respect to a subarray. Also known as "first pixel to last pixel" time.

The distinctions between these 2 categories are best understood in the context of the times used by the calibration pipeline, APT, and ETC as described in the following sections. Readout pattern terms throughout this article are shown graphically in Figure 1.

For convenience, short descriptions of all quantities presented in the JWST ETC **Reports** pane, including the times described in this article, can be found in [JWST ETC Reports](/jwst-exposure-time-calculator-overview/jwst-etc-outputs-overview/jwst-etc-reports).

**Figure 1. Definition of readout pattern terms.**

![](/files/154687382/154687388/1/1710352167974/group_int_exp_diagram.png)

*Click on the figure for a larger view.*

## Exposure time

The term *exposure time* is a generic phrase in astronomy but has a specific meaning in the context of the JWST instrument detectors. Exposure time is an array-based time, the time from the first reset of the first pixel to the final read of the last pixel in the array, and is defined as the time the detector is operating during a single expose command (i.e., set of integrations). This includes the time for reset frames and dropped frames at the beginning or end of an integration (Figure 2), but does not otherwise include any [observatory overheads](/jwst-general-support/jwst-observing-overheads-and-time-accounting-overview/jwst-observing-overheads-summary) or [instrument overheads](/jwst-general-support/jwst-observing-overheads-and-time-accounting-overview/jwst-instrument-overheads). This time corresponds to the “Single Exposure Time” quantity in the ETC Reports and the `TELAPSE` keyword in FITS headers. APT does not report the individual exposure time, only the total exposure time (see below).

Two additional quantities are reported in the ETC: "Total Exposure Time" and "Total Time Required for Strategy." The "Total Exposure Time" is the "Single Exposure Time" multiplied by the ***Total Dithers*** quantity and corresponds to the "Total Exposure Time" in APT templates. The "Total Time Required for Strategy" is the "Total Exposure Time" multiplied by the number of "pointings." These 2 quantities are different only when using the NIRSpec IFU, MIRI MRS, or MIRI MRS time-series modes and the [***IFU On-Target and Off-Target Pointing*** strategy](/jwst-exposure-time-calculator-overview/jwst-etc-calculations-page-overview/jwst-etc-strategies/jwst-etc-ifu-strategies), in which case the "Total Time Required for Strategy" is double the "Total Exposure Time," representing the 2 different "pointings." The pipeline does not report either of these quantities.

**Figure 2. Exposure time diagram.**

![](/files/154687382/154687387/1/1710352167982/exp_time_diagram.png)

*Click on the figure for a larger view.*

## Measurement time

The *measurement time* is a pixel-based time between the first and last reads of any individual pixel in an integration, multiplied by the number of integrations per exposure (Figure 3). This time does not account for resets between integrations or groups that are rejected at the beginning or end of an integration. This corresponds to the "Time Between First and Last Measurement, per exposure" in the ETC and the `TMEASURE` keyword in FITS headers. This quantity is not reported by APT.

The ETC uses the measurement time to compute the signal-to-noise ratio (SNR) for a given calculation and the pipeline implicitly uses this time for slope calculations.

**Figure 3. Measurement time diagram.**

![](/files/154687382/154687389/1/1710352167930/meas_time_diagram.png)

*Click on the figure for a larger view.*

## Saturation time

The *saturation time* is the time between the reset of a pixel and the final read of that pixel in an integration (Figure 4), which is relevant for determining how close a given pixel may get to saturation. It is close to, but not quite, the full amount of time between resets when a pixel is collecting photons; the time after the final read of a pixel is not included because the photons incident on the pixel after that time are never read. This corresponds to the "Time Between First Reset and Last measurement, per integration" in the ETC and the `EFFINTTM` keyword in FITS headers. This time is not explicitly reported by APT but can be calculated by dividing the "PhotonCollect" quantity in the "times" file by "Integrations/Exp."

The ETC uses the saturation time, along with target brightness information and [detector full well depth](/jwst-exposure-time-calculator-overview/jwst-etc-calculations-page-overview/jwst-etc-saturation), to determine whether or not saturation has occurred.

**Figure 4. Saturation time diagram.**

![](/files/154687382/154687390/1/1710352167917/sat_time_diagram.png)

*Click on the figure for a larger view.*

## Other

The ETC also reports the "Fraction of Time Spent Collecting Flux," which is the fractional time spent collecting photons during an exposure. It is defined as the "Time Between First Reset and Last Measurement, per integration" multiplied by the number of integrations per exposure, then divided by the "Single Exposure Time." This quantity is a measure of the efficiency of an observation.

---

The data products created by the JWST science calibration pipeline include a variety of time-related FITS header keyword, each of which may be useful for different purposes.  A summary of these keywords is given below, see the [JWST Keyword Dictionary](https://mast.stsci.edu/portal/Mashup/Clients/jwkeywords/) for the detailed equations.

* `MJD-BEG,` `MJD-MID`, and `MJD-END`
  + FITS-standard keywords, located in the "SCI" FITS extension header. These give the start, midpoint, and ending time for a given exposure in Modified Julian Days (MJD)
  + Identical to the `EXPSTART`, `EXPMID`, and `EXPEND` keywords in the primary FITS header (non-standard keywords included for backwards compatibility)
* `TDB-BEG`, `TDB-MID`, and `TDB-END`
  + Located in the "SCI" FITS extension header. These give the start, midpoint, and ending Barycentric Dynamical Time for a given exposure.
* `TELAPSE`
  + FITS-standard keyword, located in the "SCI" FITS extension header. This gives the total [exposure time](#JWSTTimeDefinitions-exptime) as defined above; the difference between `MJD-BEG` and `MJD-END`.
  + Identical to the `DURATION` keyword in the primary FITS header (non-standard keyword included for backwards compatibility)
  + APT equivalent: "Total Exposure Time" divided by "Total Dithers"
  + ETC equivalent: "Single Exposure Time"
* `EFFINTTM`
  + Located in the primary FITS header. This gives the [saturation time](#JWSTTimeDefinitions-sattime) as defined above.
  + APT equivalent: "Photon Collect Time" divided by "Integrations/Exp"
  + ETC equivalent: "Time Between First Reset and Last Measurement, per integration"
* `TMEASURE`
  + Located in the primary FITS header.  This gives the [measurement time](#JWSTTimeDefinitions-meastime) as defined above, which is typically most relevant for SNR purposes. Note that this is a new keyword in **jwst** pipeline version 1.14.0 (build 10.2) and later.
  + APT equivalent: None reported
  + ETC equivalent: "Time Between First and Last Measurement, per exposure"
* `XPOSURE`
  + FITS-standard keyword, located in the "SCI" FITS extension header. This is similar to `TELAPSE` as defined above, but does not include time for any resets.
  + Identical to the `EFFEXPTM` keyword in the primary FITS header (non-standard keyword included for backwards compatibility)

---

# Interpreting Level 3 times

Stage 3 processing (i.e., Image3 or Spec3) may combine data from different detectors, dithers, mosaic tiles, or gratings and the header keywords described above require some additional interpretation. There are complexities when reporting the time values given that, e.g., pixels in the overlapping region of mosaic tiles or wavelengths covered by adjacent gratings will have longer actual observing durations. The pipeline does not attempt to account for these complexities and actually handles different observing modes in different ways. This can be non-intuitive, so we provide some examples below.

Consider a NIRSpec IFU observation with the G140H/F100LP combination and a 4-point dither pattern. In this situation, there are data from 2 detectors (NRS1 and NRS2, since this is an H grating) and 4 dithers that are being combined into the Level 3 file. The time reported for `EFFINTTM` will remain unchanged between the Level 2 and 3 files, but the `TELAPSE`/`DURATION`, `TMEASURE`, and `XPOSURE`/`EFFEXPTM` values will be multiplied by a factor of 8 (2 detectors x 4 dithers) in the Level 3 header. The pipeline does not consider that the NRS1 and NRS2 detectors are simultaneously illuminated when calculating these values, it simply computes the total.

In the case of a NIRCam short-wavelength imaging mosaic using the B module (4 detectors) with, e.g., 9 mosaic tiles and 4 dithers per tile, the Level 2 quantities are multiplied by a factor of 36. In this case, the pipeline does consider that the 4 short-wavelength detectors are simultaneously illuminated and does not add the time from all of the NIRCam module B detectors.

For the MIRI MRS, stage 3 does not combine all 12 sub-bands, but it does combine the observations from a single channel (i.e., channel 1) taken with different grating positions (i.e., ***SHORT***, ***MEDIUM***, ***LONG***). The times reported in the Level 3 file are as expected compared to the Level 2 values: assuming the same observing parameters (groups, integrations, readout pattern, etc.) for each grating position, the multiplicative factor for the reported times between Level 2 and 3 is computed as the number of dithers multiplied by the number of grating positions.

---

# References

[Holler, B., et al. 2021, *JWST-STScI-006013, SM-12, Rev. A*](https://www.stsci.edu/files/live/sites/www/files/home/jwst/documentation/technical-documents/_documents/JWST-STScI-006013.pdf) (PDF)  
Consistent Times and Repetition Factors in ETC and APT

---

```

```