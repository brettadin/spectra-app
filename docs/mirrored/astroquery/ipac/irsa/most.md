|  |  |
| --- | --- |
| ****General**** | |
| ra1, dec1, ra2, dec2, etc. | Right ascension and declination of the 4 corners of the image (deg, J2000) |
| match | match = 1 indicates a matched image (added by Most) |
| ****WISE/NEOWISE**** | |
| crpix1, crpix2 | Center of image (pixels) |
| crval1, crval2 | Center of image (deg, J2000) |
| equinox | Equinox of coordinates |
| band | WISE band number; 1 (3.4 microns), 2 (4.6 microns), 3 (12 microns), 4 (22 microns) |
| scan\_id | Identification of pole-to-pole orbit scan |
| date\_obs | Date and time of mid-point of frame observation UTC |
| mjd\_obs | MJD of mid-point of frame observation UTC |
| dtanneal | Elapsed time in seconds since the last anneal |
| moon\_sep | Angular distance from the frame center to the Moon (°) |
| saa\_sep | Angular distance from the frame center to South Atlantic Anomaly (SAA) boundary (deg) |
| qual\_frame | This integer indicates the quality score value for the Single-exposure image frameset, with values of 0 (poor| quality), 5, or 10 (high quality) |
| image\_set | image\_set=4 for 4band, 3 for 3band, 2 for 2band, and 6, 7 etc. for NEOWISE-R year 1, 2 etc. |
| ****2MASS**** | |
| ordate | UT date of reference (start of nightly operations) |
| hemisphere | N or S hemisphere |
| scanno | Nightly scan number |
| fname | FITS file name |
| ut\_date | UT date of scan (YYMMDD) |
| telname | Telescope location - Hopkins or CTIO |
| mjd | Modified Julian Date of observation |
| ds | ds=full for 2mass |
| ****PTF**** | |
| obsdate | Observation UT date/time YYYY-MM-DD HH:MM:SS.SSS |
| obsmjd | Modified Julian date of observation |
| nid | Night database ID |
| expid | Exposure database ID |
| ccdid | CCD number (0…11) |
| rfilename | Raw-image filename |
| pfilename | Processed-image filename |
| ****ZTF**** | |
| obsdate | Observation UT date/time YYYY-MM-DD HH:MM:SS.SSS |
| obsjd | Julian date of observation |
| filefracday | Observation date with fractional day YYYYMMDDdddddd |
| field | ZTF field number |
| ccdid | CCD number (1…16) |
| qid | Detector quadrant (1…4) |
| fid | Filter ID |
| filtercode | Filter name (abbreviated) |
| pid | Science product ID |
| nid | Night ID |
| expid | Exposure ID |
| itid | Image type ID |
| imgtypecode | Single letter image type code |
| ****Spitzer**** | |
| reqkey | Spitzer Astronomical Observation Request number |
| bcdid | Post Basic Calibrated Data ID (Lvl. 2 product search) |
| reqmode | Spitzer Astonomical Observation Request type |
| wavelength | Bandpass ID |
| minwavelength | Min wavelength (microns) |
| maxwavelength | Max wavelength (microns) |
| time | UT time of observation |
| exposuretime | Exposure time (sec) |