Data products from all JWST instruments are stored in the [Mikulski Archive for Space Telescopes](http://archive.stsci.edu/) (MAST), which is the permanent repository and access portal for many NASA UV/optical/IR missions and selected ground-based surveys. These archived data products include raw uncalibrated exposures, all levels of calibrated data products, and contemporaneous engineering and guide star data. [High-level science products](https://mast.stsci.edu/hlsp/#/) contributed by investigating teams are also available.

This article provides a basic overview of the JWST data ecosystem, with links to information about the data products formats, how to find and download them, and how to cite them in scientific publications. Links are additionally provided throughout to the more extensive [MAST User Documentation](https://outerspace.stsci.edu/display/MASTDOCS).

Note that this article and its child pages in the page tree provide generic information about pipeline data products across different release versions. If you're looking for specific calibration information about the latest JWST data products, see [JWST Calibration Status](/jwst-calibration-status). You can also learn [what's new](/jwst-science-calibration-pipeline/jwst-operations-pipeline-build-information#JWSTOperationsPipelineBuildInformation-whatsnew) in the latest build, what's [coming soon](/jwst-science-calibration-pipeline/jwst-operations-pipeline-build-information#JWSTOperationsPipelineBuildInformation-comingsoon) for that build, and a list of current [known issues with JWST data](/known-issues-with-jwst-data).

---

# Authentication

Science data obtained from JWST will be released to the astronomical community following an [*exclusive access period*](/accessing-jwst-data/exclusive-access-period)  *(EAP)*, during which the principal investigating team enjoys exclusive scientific use.

Investigator team members who wish to access data within the EAP must have an [STScI MyST](https://proper.stsci.edu/proper/authentication/auth) account to establish electronic credentials to *authenticate* their identity. PIs and CoIs of JWST observing programs already have MyST credentials, which they used to submit their proposals for review, but team members added after proposal submission (e.g., post-docs or graduate students) will need to establish an account if one does not already exist. When you wish to retrieve EAP data you must be logged in to a MAST application or have an [Auth.MAST](https://auth.mast.stsci.edu/info) token if using an API (see [MAST Accounts](https://outerspace.stsci.edu/display/MASTDOCS/MAST+Accounts) for details). Investigator team members must also be *authorized* to access data from their programs. PIs will automatically receive such authorization, which they may also grant to any collaborator who is registered with the STScI MyST.

Data for which the exclusive access period has expired may be retrieved anonymously from MAST. A MyST account is *not* *required* to search, view, explore with MAST tools, or retrieve data that have been released to the public.

---

# JWST data overview

A high-level guide to JWST science data products can be found at [JWST Science Data Overview](/accessing-jwst-data/jwst-science-data-overview). New users are encouraged to start there to learn about the different stages of data processing to help determine which data products they are most interested in retrieving. More generally, there are various types of JWST data available:

* Science data, including products from uncalibrated, intermediate, and calibrated/combined stages of processing
  + Reference files used to calibrate science data
  + Concomitant guide star data
* Metadata for planned (but unexecuted) observations
* Concomitant calibrated engineering data
* Episodic wavefront sensing data

All of these products are available from MAST using one or a choice of user interfaces, as explained in the following subsections. The table below summarizes which interfaces to use for a given data type or feature, including whether users may subscribe for notifications of events such as reprocessing or data becoming public.

---

# Retrieving JWST data from MAST

There are multiple methods to search and retrieve data from MAST, each with their own advantages; an overview is provided below. Please also refer to the [MAST Primer for JWST](https://outerspace.stsci.edu/display/MASTDOCS/MAST+Primer+for+JWST) (which contains step-by-step instructions for common searches and retrievals) and the [MAST FAQ](https://outerspace.stsci.edu/display/MASTDOCS/FAQ) (which has answers to common user questions), as well as [JWebbinars](https://www.stsci.edu/jwst/science-execution/jwebbinars) 17 and 25 which featured presentations and tutorials on using MAST applications and APIs.

Note that the exact names of JWST files in MAST can change over time as the pipeline and the latest installed [pipeline build](/jwst-science-calibration-pipeline/jwst-operations-pipeline-build-information) evolve.

## Web interfaces

### MAST Portal

The [Portal interface](https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html) is the default method of interacting with the MAST database, through which users can find all varieties of JWST data products along with co-spatial products from any other hosted mission archives, and overlay science datasets from other missions and surveys. The Portal is recommended for all first-time users as well as those interested in multi-mission capability, and includes the ability to search by observing program, instrument mode, sky coordinates, or astrophysical source name.

The  [JWST Engineering Data (EDB) Portal](https://mast.stsci.edu/portal/Mashup/Clients/jwstedb/jwstedb.html) allows users to query the engineering database for spacecraft telemetry that may not be associated with a specific science program. Most engineering data are not restricted, and may be retrieved by any authenticated user (i.e., they must be logged in to MAST to retrieve these data). This is an expert search interface, relying on users to know the specific mnemonic names for the telemetry that they wish to retrieve, and the time range in which to retrieve them; for example, the mnemonic `SA_ZATTESTn` (where the value *`n`* ranges from 1 through 4) defines the coefficients of the quaternion describing the pointing and roll of the spacecraft. See[Using the Engineering Data Portal](https://outerspace.stsci.edu/display/MASTDOCS/Using+the+Engineering+Data+Portal) for further information.

Note that the MAST Science Portal interface also provides a direct link to the Engineering Data Portal (EDB). After querying the portal for science data, the search results table will contain a link to populate an EDB search with the time range corresponding to the selected science data products.

The Portal can also be used to generate [subscriptions to program data](https://outerspace.stsci.edu/display/MASTDOCS/Program+Subscriptions+and+Notifications), allowing users to be automatically notified when new and/or reprocessed data is available for a given observing program, or when previously exclusive-access data becomes public.

A basic user guide can be found at the [MAST Web Access](/accessing-jwst-data/mast-web-access) page, with more extensive documentation available in [Outerspace Portal Guide](https://outerspace.stsci.edu/display/MASTDOCS/Portal+Guide).

Browser Pop-ups

The MAST Portal interface requires that*pop-up blockers be disabled* for the domain <https://mast.stsci.edu/> in order to download data. Check the documentation for your browser to determine how this is done, and be alert for notifications from the browser that popups are being blocked. In many cases it simply requires giving approval for popups when you are asked.

### JWST Mission Search

The [JWST Mission Search](https://mast.stsci.edu/search/ui/#/jwst/) form is an alternative method of querying that offers a much larger variety of mission-specific search criteria (e.g., time-series observations) and can accept uploaded object lists to search for. However, this search method is limited to JWST data alone and does not yet include data preview capabilities comparable to the Portal interface. This is a new search interface (first offered in November 2023), and for now has [some limitations](https://outerspace.stsci.edu/display/MASTDOCS/Mission+Search+Caveats).

A guide to the Mission Search form can be found at the [Outerspace Mission Search Guide](https://outerspace.stsci.edu/display/MASTDOCS/Mission+Search+Guide).

## Programmatic interfaces

The MAST Application Programming Interfaces (APIs) allow users to discover and retrieve JWST data through scripted queries in common programming languages, instead of going through the standardized web interface. These interfaces require some level of programming experience, but they afford a correspondingly greater degree of complexity and customization in searches and retrievals. Through this mechanism the user may also cast a wider search net in an effort to discover any and all data related to a particular object or location. Likewise, the API allows data retrieval to be embedded into custom frameworks such as Jupyter notebooks.

There are some circumstances in which using the API is essential for searching and retrieving JWST data. Programs that produce very large numbers of data products (tens of thousands) per Observation for instance can overload the MAST Portal download basket, and must instead be retrieved via the API.

Information about the MAST API can be found on the [MAST API Access](/accessing-jwst-data/mast-api-access) page.

### Amazon Web Services (AWS)

Publicly-available data can be retrieved from the [MAST AWS cloud registry](https://registry.opendata.aws/collab/stsci/); further information can be found on the [MAST API Access](/accessing-jwst-data/mast-api-access) page.

Virtual Observatory protocols also enable users to discover and retrieve data from astronomical archives, including within the MAST Portal. The methods are rather extensive, and are described in more detail in the MAST article [Virtual Observatory](https://archive.stsci.edu/virtual-observatory). Note that these tools currently lack the ability to provide user authentication credentials to archive services, and so *cannot be used to retrieve data archived within the exclusive access period*.

---

# Data product versions

As discussed by [JWST Operations Pipeline Build Information](/jwst-science-calibration-pipeline/jwst-operations-pipeline-build-information), the JWST science calibration pipeline and associated reference files are updated according to a quarterly build schedule.  All JWST observations are reprocessed with each build, and the science data products available for download from MAST will thus update quarterly as well.  Typically, new versions of the data products are available within a few weeks after a given build is made operational.

* If using the [JWST Mission Search](https://mast.stsci.edu/search/ui/#/jwst/) form, the version of the jwst calibration pipeline used to create a given data product is given by the 'Calibration software version' column. As of May 2025, this is a default column returned by all searches.
* If using the [Portal interface](https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html), the version of the jwst calibration pipeline used to create a given data product is given by the 'Calibration Version' information in the Summary panel within the Download Manager.
* The calibration pipeline version can also be obtained from the `CAL_VER` keyword in the primary extension header of any JWST FITS file.

---

# User support

[MAST](https://archive.stsci.edu/) staff members will assist the general science community with issues related to archived data, searches, notifications, the use of visualization tools, and standard or scripted data access and retrievals. Contact the Archive help desk by one of the following means:

Or, visit [Archive Support](https://outerspace.stsci.edu/display/MASTDOCS/Archive+Support) for a full list of support topics. It may be worth visiting the [MAST JWST Data FAQ](https://outerspace.stsci.edu/display/MASTDATA/MAST+JWST+Data+FAQ) to see if your question has already been addressed.

**High-level science products**

Archive science staff also assist JWST PI and Archival research teams in preparing [high-level science products (HLSPs)](https://archive.stsci.edu/hlsp) that will be hosted by MAST. HLSPs are required deliverables of funded JWST Archival research programs, but are encouraged from any science team that uses JWST data as a part of their research. These data products should provide substantial science value to the general astronomical community, and have broader appeal beyond the original scope of the science goals for a particular program.

**Requirements for HLSP contributions**

In order to enable meaningful searches on contributed datasets, and to provide a consistent and comprehensive set of metadata to users, there are a variety of requirements and recommendations for contributed data collections. See the [HLSP Contributor Guide](https://outerspace.stsci.edu/display/MASTDOCS/HLSP+Contributor+Guide) for details.

---

# Citing JWST data

It is important for investigators who publish scientific results based on MAST data to acknowledge the mission and (if applicable) the source of funding.  Likewise, it is important to cite the JWST data that were analyzed in the publications, which one can do by creating digital object identifiers (DOIs) using a MAST tool. See [Citing JWST Data](/accessing-jwst-data/citing-jwst-data) for details.

---