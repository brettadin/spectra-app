MAST provides web (browser-based) user interfaces to search, preview, select, and retrieve JWST data products. Most of these capabilities are also available via programming interfaces (see MAST APIs) but those require some level of programming expertise, and do not by themselves enable visualization of the results. This article describes the features of the two main web user interface choices, highlight their strengths, and refer to extensive documentation on their use. 

The two web user interfaces for searching science data are the [MAST Portal](https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html) and the newer [JWST Mission Search](https://mast.stsci.edu/search/ui/#/jwst/). The features of each are summarized in the table below, where features to be added soon to the JWST Mission Search are indicated (![hammer and wrench](/plugins/servlet/twitterEmojiRedirector?id=1f6e0 "hammer and wrench")). Note the following:

* Ancillary data: guide star data and calibration reference files
* Planned Obs: planned but not yet executed observations
* Data Browser: embedded tools for visualizing data
* Subscriptions: the ability to subscribe to notifications about the arrival or reprocessing of data in MAST

| Web Interface | Science Data | Ancillary Data | Planned Obs | Sky Viewer | Previews | Data Browser | Subscriptions | Retrieval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Portal | Cross-mission | (tick) | (tick) | (tick) | (tick) | (tick) | (tick) | (tick) |
| JWST Mission Search | JWST specific | (tick) | hammer and wrench | (error) | hammer and wrench | hammer and wrench | (error) | (tick) |

Both interfaces display search results in a table, one match per row, from which you can select specific data to retrieve. The background color of the table rows indicates the availability of the data: Public (clear), Exclusive Access (light yellow), and Planned but un-executed (light orange; Portal only).

---

# Searching for data

## Portal search

The Portal has a rich set of features, which take some time to explore (see the [Portal Guide](https://outerspace.stsci.edu/display/MASTDOCS/Portal+Guide) for details). It is the interface of choice to search simultaneously for data from all MAST missions. Exploring data begins with a successful search for JWST or other data that meet your scientific criteria. Figure 1 shows the results of a simple query of a target name in the Portal. The following tutorials may be helpful for new Portal users:

**Figure 1. Result of a Portal query for the object *M51***

![](/files/154687391/154687396/1/1706129188968/query_m51.png)

*Click on the figure for a larger view.*

In this example, the search is filtered for GALEX and WFC3/IR images, with selected observations from the results table highlighted in the**AstroView** panel.

### The Portal window

See the article [Field Guide to the Portal](https://outerspace.stsci.edu/display/MASTDOCS/Field+Guide+to+the+Portal) in the MAST [Portal Guide](https://outerspace.stsci.edu/display/MASTDOCS/Portal+Guide) for a tour of the anatomy of the Portal interface. Three main panels and a toolbar provide tools for selecting and visualizing the search results. These features are described in detail in the Portal Guide chapter [Browsing Data](https://outerspace.stsci.edu/display/MASTDOCS/Browsing+Data), and are summarized briefly below. Following exploration and visualization, the next step will be selecting data for download, as discussed in the [Retrieving data](#MASTWebAccess-retrieve) section.

#### Left panel: refine the search

The leftmost panel of the results page provides a number of *filters* to isolate specific data characteristics of interest. These include product types (image, spectrum, time series, etc.), mission (HST, SWIFT, FUSE, etc.), instrument, optical elements, etc. See [Refining Results with Filters](https://outerspace.stsci.edu/display/MASTDOCS/Refining+Results+with+Filters) in the Portal Guide for details.

#### Middle panel: select and preview results

Words in **bold** are GUI menus/  
panels or data software packages;   
***bold italics***are buttons in GUI  
tools or package parameters.

The results of a search, as modified by filters, are presented in tabular form in the center panel, one result per row. See the article

[Search Results Grid](https://outerspace.stsci.edu/display/MASTDOCS/Search+Results+Grid)

in the

[Portal Guide](https://outerspace.stsci.edu/display/MASTDOCS/Portal+Guide)

for details. Just above the table is a

*toolbar*

that provides options for viewing and manipulating metadata, and for bulk selections of results. The table itself provides tools for choosing which fields in the results to display (i.e., metadata like the mission, instrument, target name, and so on), tools to visualize data (i.e., viewers for spectra or time series) and an option to overlay an image in the

**AstroView**

tool. Each row also includes a selection checkbox for placing results into the

[Download Basket](https://outerspace.stsci.edu/display/MASTDOCS/Download+Basket)

for retrieval.

Among the options for data visualization in the results table is the Jdaviz tool, which was built for JWST data. You can use it to browse JWST spectra (MOS, IFU, fixed slit, etc.). See the [JWST Data Analysis Visualization Tool](https://jdaviz.readthedocs.io/en/latest/) documentation for details. This tool may be used standalone on your desktop, in Jupyter Notebooks, or (for MAST) in a web application. The "Jda" tool icon will appear in the ***Actions*** menu of the MAST Portal results table.

![](/files/154687391/154687395/1/1706129189392/mast_jdaviz_new_portal_icon.png)

When selected, you can open the tool for visualization. See the [Data Visualization](https://outerspace.stsci.edu/display/MASTDOCS/Data+Visualization) article in the [JWST Archive Manual](https://outerspace.stsci.edu/display/MASTDOCS/JWST+Archive+Manual) for details.

The right side of the Portal search results displays the **AstroView** panel, which displays a sky-survey background of the target area, overlaid with wireframe spatial footprints of the matched observations. See the [AstroView](https://outerspace.stsci.edu/display/MASTDOCS/AstroView) article in the Portal Guide to learn how to customize this tool, and to use color to highlight observations with different instruments or observatories.

```

```

---

## JWST Mission Search

The [JWST Search](https://mast.stsci.edu/search/ui/#/jwst/) application is the newest MAST interface for searching and retrieving data from JWST. It is restricted to JWST science and ancillary data, and offers a very rich set of metadata for selecting specific kinds of data. It is also very much more performant, in that it finds and selects data much faster (up to 30x), and can retrieve much larger volumes of data through the browser, compared to the Portal. Users can specify search criteria very flexibly, and there is immediate feedback (just below the ***Search*** button) on the number of matching datasets. See the [Mission Search Guide](https://outerspace.stsci.edu/display/MASTDOCS/Mission+Search+Guide) for further information. There are a number of [caveats](https://outerspace.stsci.edu/display/MASTDOCS/Mission+Search+Caveats) for this interface, such as the lack of planned observations and the inability to search purely for guide star products; these will be addressed in future releases. The search interface is shown in Fig. 3.

**Figure 2. JWST Mission Search interface, initial search form.**

![JWST Mission Search user interface](/files/154687391/154687394/1/1708637180202/JWST_MM_search.png)

*Click on the figure for a larger view.*

After pressing the ***Search*** button, the results are displayed in a table, one row per dataset. It is from this table view that datasets can be selected for retrieval.

---

# Selecting data

After executing a search for data in MAST using any of the interfaces, the next step is to select observations or datasets for download. It is also possible to further refine the selection of specific types of files (e.g., stages of products, guide star data, calibration reference files, etc.) that are implicitly included in each row. The Portal uses the [Download Basket](https://outerspace.stsci.edu/display/MASTDOCS/Download+Basket) for selecting files, and the JWST Mission Search uses the [Download Overlay](https://outerspace.stsci.edu/display/MASTDOCS/Download+Overlay) (see figures and notes on special features, below). Both provide a mechanism for selecting contemporaneous guide star data and the calibration reference files that were used by the JWST pipeline. 

Both interfaces can restrict the available data products to the subset that has been identified as essential for extracting the intended science from the data. See the [Minimum Recommended Products](https://outerspace.stsci.edu/display/MASTDOCS/Minimum+Recommended+Products) (MRP) article for details.

## Portal download basket

**Figure 3. The Portal download basket**

![MAST Portal download manager, showing file filtering and selection](/files/154687391/154687392/1/1708956268628/Portal_Basket.png)

*Click on the figure for a larger view.*

The Portal groups search results by ***Observation ID***. This means results appear in the table by the name of the highest-level product (usually level-3), even though all other products, including uncalibrated data, are included implicitly.

MRP Checkbox

MRP products are selected by default in the MAST Portal. The MRP checkbox in the **Download Manager** must be de-selected in order to view and retrieve raw- and intermediate-level data products, and all ancillary products including guide star data.

Some observations in the Portal search results table are associated with a very large number of files. Attempting to load too many such observations into the basket at once can result in an error. This problem is particularly likely for observations with many extracted spectra (e.g., NIRCam wide field slitless spectra), or observations containing lots of spatial dithers or other spacecraft maneuvers (as for an extended mosaic of a field or for moving targets). In these cases using the JWST Mission Search or a MAST API are the best alternatives for data retrieval. See the article [Using MAST APIs](https://outerspace.stsci.edu/display/MASTDOCS/Using+MAST+APIs).

## JWST Mission Download overlay

**Figure 4. File download overlay, for selecting the specific files or types of files to retrieve**

![JWST Mission Search download manager](/files/154687391/154687393/1/1708955902939/JWST_MM_DownloadOverlay.png)

*Click on the figure for a larger view.*

The JWST Mission Search lists search results by ***Dataset ID***, rather than ***Observation ID***. This has the effect of grouping levels 1 and 2 search results together, separate from level 3. Therefore selecting all levels of data products for download requires that the appropriate rows be selected in the results table.

This form of search identifies data files much more efficiently than the MAST Portal, and is not subject to the same limits on the number of selected files for download as the Portal.

---

# Retrieving data

Science observations identified with either web interface may be retrieved as a bundle (a zip or tar file) using one of the methods summarized below. For detailed instructions, see the following references:

Browser Pop-ups

The MAST Portal interface requires that*pop-up blockers be disabled* for the domain <https://mast.stsci.edu/> in order to download data. Check the documentation for your browser to determine how this is done, and be alert for notifications from the browser that popups are being blocked. In many cases it simply requires giving approval for popups when you are asked.

## Direct download

Both user interfaces offer an option for a direct (streaming) download through the browser of the MRP files associated with a single row in the results table, without the need for selecting individual files. The JWST Mission Search also offers the choice of downloading all files, not just the MRP subset.

## Download Manager/Overlay

The Download Manager and the Download Overlay both support two main options for retrieval. The first is streaming download of a file bundle through the browser, where the selected data files will be bundled into a .tar, .tar.gz, or .zip file and transferred to your machine. The second option is to create a downloadable script that contains commands for downloading the selected files outside of the browser session (see next subsection).

Size Limitation

Portal data retrievals via immediate download are limited to about 20,000 files. Larger transfers require an asynchronous retrieval method: a cURL script, staging data for FTP retrieval, or the MAST API.

The Portal offers a third option: *staging* data for later retrieval from the MAST FTP server.

## Script or batch

Both interfaces offer a choice to download a script, which will contain curl commands to download the selected files to your platform, one at a time. This is a good choice if the data volume is very large, or if the internet connection is subject to intermittent interruptions. It can also be shared with your colleagues if they also need to retrieve the same files. To use the script, simply execute it in a Unix shell, and provide login credentials when prompted, to initiate the secure transfer of all selected files. The script contains a sequence of [cURL](https://www.geeksforgeeks.org/curl-command-in-linux-with-examples/) commands, which are relatively robust against connection interruptions and other foibles of internet file transfers.

The Portal also offers a batch retrieval option, which will stage your data on the MAST FTP server for subsequent retrieval. You will be notified via e-mail when the transfer is complete and will be given the server address and path to the staging directory. Note that your file transfer client must be configured to use FTPS, rather than FTP; Mac users will need to use a third-party secure file transfer client, such as [Cyberduck](https://cyberduck.io/) to retrieve the data from the server. For other retrieval options, see the [Retrieval Methods](https://outerspace.stsci.edu/display/MASTDOCS/Retrieval+Methods) article in the Portal Guide.

Note that a valid email address must be provided for batch data retrieval requests, though an [STScI MyST ID](https://proper.stsci.edu/proper/authentication/auth) is not required for public data.

## What's in the box

All data products for all selected observations will be bundled together in a zip or tar file for delivery. When the bundle is unpacked, data for each observation will appear in one of two ways:

* a separate subdirectory for each observation (Portal) or dataset (JWST Mission Search)
* a single directory containing all files (available only with JWST Mission Search)

The download manifest

The zip (or tar) file will include a file called **"**MANIFEST.HTML"which lists each file name, a short description, and whether access is restricted. It will also note any files that could not be downloaded and the reason why (e.g., if you do not have permission to retrieve them).

For the Portal only, the data bundle includes by default the highest-level data products, *plus all parent data* (unless those data have been de-selected in the download manager) For example, if an observation/visit/exposure/detector combination resulted in level-2 data products, all level-1 products would automatically be included unless the user explicitly chooses otherwise. Note: level-3 products will appear in separate directories.

---

# Additional Portal features

The Portal offers a number of additional capabilities beyond searching and retrieving science data, including:

---

```

```