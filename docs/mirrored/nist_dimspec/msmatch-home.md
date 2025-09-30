The MSMatch application installs alongside DIMSpec. If there is continued (or expanded) interest, the project could be turned into an R package installable directly from GitHub with additional development or this tool can be deployed to a shiny server to avoid the need for launching or maintaining it locally. For now, this application is distributed for demonstration and evaluation with an implementation of NIST DIMSpec containing high resolution accurate mass spectrometry data for per- and polyfluorinated alkyl substances (PFAS). The R project can be opened in [RStudio](https://www.rstudio.com/) which may be downloaded and installed free of charge if not already installed. Initial set up does require an internet connection to install dependencies; on a system which does not contain any software components this can take a considerable amount of time.

### Input File Format Requirements

To use MSMatch, raw data files produced by a mass spectrometer must be converted into mzML format ([Deutsch 2010](#ref-deutsch_mass_2010)) using [Proteowizardâs](https://proteowizard.sourceforge.io/) msConvert software ([Chambers et al. 2012](#ref-chambers_cross-platform_2012)). There are specific parameters that must be used during conversion.

```
Filter: Threshold peak filter
Threshold type: absolute
Orientation: most intense
Value: 1
Filter: Peak picking
Algorithm: vendor
MS levels: 1-2
```

A more detailed user guide for converting the files is provided as a [vignette](file_convert.pdf).

### Launching MSMatch

Launch this tool similarly to other âshinyâ-based tools provided as part of DIMSpec. In brief, this can be done from a terminal or the R console, though the preferred method is to use RStudio ([RStudio Team 2020](#ref-RStudio)). The following commands are typical given an existing installation of R or RStudio and should always be run from the project directory. The shiny package ([Chang et al. 2022](#ref-R-shiny)) and other necessary R packages will be installed if it not already available by running the script at `R/compliance.R`, but shiny is the only package required to start the application. When first run, it may take a moment to install necessary dependencies and launch the application programming interface (API) server.

*Terminal*

> R.exe âshiny::runApp(âinst/apps/msmatchâ)â

*R console*

> `shiny::runApp(âinst/apps/msmatchâ)`

*RStudio*

> Open the â.Rprojâ project file in RStudio, navigate to the
> âinst/apps/msmatchâ directory, open one of the âglobal.R,â
> âserver.R,â or âui.Râ files, and click the âRun Appâ button. Files
> open in an RStudio project will remain open by default when RStudio is
> closed, allowing users to quickly relaunch by simply loading the
> project. For best performance, ensure âRun Externalâ is selected from
> the menu âcarrotâ on the right to launch the application in your
> systemâs default web browser. This application has been tested on
> Chrome, Edge, and Firefox.

Alternatively, once the compliance script has been executed MSMatch can be launched using `start_app("msmatch")`.

Once launched the API server will remain active until stopped, allowing users to freely launch, close, and relaunch any shiny apps dependent upon it much more quickly. The application is fluid and will dynamically resize to fit the dimensions of a browser window. By default, the server does not stop when the browser is closed. This means that, once started, it is available by navigating a web browser back to the URL where it launched until the server is shut down.

If anything is needed from the user, interactive feedback will occur in the console from which it was launched. Install any packages required if prompted by the application. Once the package environment requirements have been satisfied and the server has spun up, which may take a moment, the tool will launch (Figure 1) either in the RStudio viewer or the browser.

### Using MSMatch

Every effort has been made to make MSMatch as intuitive for users as possible. Set up may require a bit of effort on certain systems, but once the application launches it should be straightforward; please contact the authors directly or email [[email protected]](/cdn-cgi/l/email-protection#7c0c1a1d0f3c12150f08521b130a) for support, or with any questions or suggestions.

Hints in the form of tooltips are provided throughout; hover over question mark icons or controls to see them. These can be toggled on and off at any time using the âShow Tooltipsâ toggle button at the bottom left of the application window (see [Figure 1](msmatch-home.html#fig04-01) inset at bottom right). If enabled, advanced search settings can be similarly toggled on and off for the session (see [Application Settings](msmatch-home.html#msmatch-application-settings) for instructions on how to set default accessibility and settings for tooltips and advanced settings). The âhamburgerâ (three short horizontal lines stacked on top of one another) icon at the top left of the screen will collapse the left-hand navigation panel to provide more horizontal room on smaller screens, though the application will rearrange itself when screens are smaller than a minimum width.

---

![](assets/fig04-01_msmatch_landing_page.png "Figure 1. The home page for the MSMatch web application contains basic information about the application and can be tailored easily for each use case for reuse.")

Figure 1. The home page for the MSMatch web application contains basic information about the application and can be tailored easily for each use case for reuse.

---

Click the âClick Here to Get Startedâ button to begin. This will activate the âData Inputâ page. Example data files are provided in the project directory (âexample/PFAC30PAR\_PFCA2.mzMLâ and âexample/example\_peaklist.csvâ).

---

![](assets/fig04-02_data_input.png "Figure 2.The data input page of MSMatch where data files, experiment parameters, and features of interest are identified. Workflow guidance options become available once data are provided.")

Figure 2. The data input page of MSMatch where data files, experiment parameters, and features of interest are identified. Workflow guidance options become available once data are provided.

---

All input values are validated against expectations and will flag the user if invalid values are used.

#### Step 1. Load an mzML Data File

MSMatch accepts files in the mzML format, see the previous section [Input file format requirements](msmatch-home.html#msmatch-file-format) for more details. Either click the âLoadâ button to select a local file or click and drag one from your file system to that widget. Only .mzML files are accepted using this release. Set instrument parameters to match those used in the experiment using the controls provided.

#### Step 2. Identify Features of Interest

Two methods ([Figure 3](msmatch-home.html#fig04-03)) are supported to identify features of interest by mass-to-charge ratio and retention time properties. Either use case is fully supported. Users may:

1. import a file (either .csv, .xls, or .xlsx, though workbooks should have relevant data in the first worksheet) and identify which columns contain the correct information ([Figure 3, left](msmatch-home.html#fig04-03)).
   * Click âImportâ and select a file of interest from your local
     computer or drag and drop a file to this input.
   * Use this method if you have a file containing features of
     interest from other procedures or software outputs to quickly
     import many feature properties.
   * Select a column that corresponds to each property.
   * To append to the current list, keep the checkbox checked. To
     overwrite, uncheck this box.
   * Click âLoad Parametersâ to validate and add parameters or
     âCancelâ to abort this operation.
   * Repeat until all files are imported.

AND/OR

2. click the âAddâ button and enter search parameters one at a time
   ([Figure 3, left](msmatch-home.html#fig04-03)); repeat this process to add more.
   * Add numeric values for all items.
   * Click âSave Parametersâ to validate and add or âCancelâ to abort
     this operation

* Users receive feedback on the form if values are left blank or if
  they do not meet expectations (e.g.Â centroid is after peak start and
  before peak end).
* Values should all be numeric in nature.
* This list may be edited after import ([Figure 4](msmatch-home.html#fig04-04)).

Data are ready to be processed once features of interest are added. Selecting any row in the resulting table makes two additional functions available ([Figure 4, right](msmatch-home.html#fig04-04)). With a row selected, click âRemoveâ to delete it or âEditâ to bring up the same form as above ([Figure 3, right](msmatch-home.html#fig04-03)), change the values, and click âSave Parameters.â All records remaining in the feature of interest list will be available to search widgets on subsequent pages.

---

![](assets/fig04-03_FOI_input_dialogs.png "Figure 3. Dialogs to identify features of interest by upload (left) or manually by clicking the Add button (right).")

Figure 3. Dialogs to identify features of interest by upload (left) or manually by clicking the Add button (right).

---

![](assets/fig04-04_FOI_list.png "Figure 4. Manage the feature identification list (left) interactively by adding, editing, or removing features as needed (right) by selecting a row from the table and clicking the appropriate button.")

Figure 4. Manage the feature identification list (left) interactively by adding, editing, or removing features as needed (right) by selecting a row from the table and clicking the appropriate button.

---

#### Step 3. Generate the Search Object

Click the âProcess Dataâ button ([Figure 5](msmatch-home.html#fig04-05)) to filter and recast data in the .mzML file according to defined feature properties. (In further screenshots the manually added row [m/z 327.4586] has been removed. This will unlock mass spectral matching actions; click one of the buttons or navigate to the desired page using the navigation panel on the left.

---

![](assets/fig04-05_process_data_button.png "Figure 5. Click âProcess Dataâ to validate experiment data and choose one of the options that appear or navigate to the desired page using the left-hand navigation menu.")

Figure 5. Click âProcess Dataâ to validate experiment data and choose one of the options that appear or navigate to the desired page using the left-hand navigation menu.

---

#### Step 4. Explore Results

Algorithmic matching of provided mass spectral data for features of interest are matched against data stored in the attached database. Matching algorithms are described in detail in [Compound and Fragment Match Algorithms](msmatch-home.html#msmatch-algorithms). In brief, data meeting properties of a feature of interest are extracted from the provided .mzML file given the reported mass accuracy settings of the experiment and mass-to-charge ratios for known compounds and fragments are searched within an uncertainty boundary range and returned from the database. Results are then stored in the application server and displayed to the user.

##### Match Compounds

Click the âCompound Matchâ button from the previous page or select âCompound Matchâ from the left-hand navigation menu to match features of interest from the mzML file to known compounds in the database.

---

![](assets/fig04-06_compound_match_screen.png "Figure 6. Compound matching options. Select a feature of interest and search type, then click the 'Search' button.")

Figure 6. Compound matching options. Select a feature of interest and search type, then click the âSearchâ button.

---

Select a feature of interest from the drop-down box and click the âSearchâ button.

In most cases the âPrecursor Searchâ option should remain selected; the other option is âAllâ which takes a considerable amount of time and may yield poor matches. The âUse Optimized Search Parametersâ checkbox will utilize a set of predefined properties for known compounds to accelerate the search; uncheck this box to perform a wider search.

Narrative results are provided regarding the top match and the match currently being viewed, including a method summary for how the reference was measured. The spectral comparison is visualized in a âbutterfly plotâ showing measurements in black and the comparison (database) spectrum in red; toggle the different fragmentation levels (e.g.Â MS1 vs MS2) to view those independently ([Figure 7](msmatch-home.html#fig04-07)).

The table at the right displays compound match identities and their match scores. Click the green plus icon to expand any given row of the table or click a different row to examine that match and update the plot and method narrative ([Figure 8](msmatch-home.html#fig04-08)). This table may be downloaded using the buttons at the bottom left of the table.

---

![](assets/fig04-07_compound_match_results.png "Figure 7. Results of a compound match for the selected feature of interest. (Inset: Download results using the buttons at the bottom left of the match table.)")

Figure 7. Results of a compound match for the selected feature of interest. (Inset: Download results using the buttons at the bottom left of the match table.)

---

![](assets/fig04-08_compound_match_change.png "Figure 8. Results change in real time when different rows are selected from the table, updating the narrative, butterfly plot, and method narrative (compare with [Figure 7](#fig04-07)).")

Figure 8. Results change in real time when different rows are selected from the table, updating the narrative, butterfly plot, and method narrative (compare with Figure 6).

---

Evaluation of match score uncertainty is also provided. Click the âEstimate Match Score Uncertaintyâ button below the butterfly plot ([Figure 7](msmatch-home.html#fig04-07)) to evaluate the spread in match scores for the currently selected match ([Figure 9](msmatch-home.html#fig04-09)). Results from a bootstrapped version of the match algorithm are displayed as boxplots for both forward and reverse matches. Toggle the different fragmentation levels (e.g.Â MS1 vs MS2) to view each. Change the number of bootstrap iterations to use and click âCalculate Uncertaintyâ to run the estimation again. Click the âCloseâ button to return to the compound match screen and change the match being evaluated. The calculation of mass spectral uncertainty and estimation of the distribution of the match scores is described in Place, Benjamin J. ([2021a](#ref-place_development_2021)).

---

![](assets/fig04-09_match_uncertainty.png "Figure 9. Estimation of match score uncertainty for any selected match candidate.")

Figure 9. Estimation of match score uncertainty for any selected match candidate.

---

The match result table (Figures [7](msmatch-home.html#fig04-07) and [8](msmatch-home.html#fig04-08)) offers several options.

* Sort using the column headers (results are by default ordered by MS1 score and MS2 score, with ties being decided by reverse match scores and the number of annotated fragments).
* Download the resulting match table by either copying it to the clipboard (âCopyâ) or downloading in either CSV or XLS file formats using the buttons at the bottom left of the table (see Figure 6).
* Select any row in the table to update the narratives and plots or evaluate match score uncertainty for that match.

If no compound matches are found, users are flagged to that effect. Proceed to Match Fragments using the navigation menu to identify fragments matching known annotations.

##### Match Fragments

Click the âFragment Matchâ button from the data input page ([Figure 5](msmatch-home.html#fig04-05)) or select âFragment Matchâ from the left-hand navigation menu to match analytical fragments within features of interest from the .mzML file with previously annotated fragments in the database.

Select a feature of interest from the drop-down box just as with compounds (features are defined in Step 2: Identify Features of Interest) and click the âSearchâ button ([Figure 10](msmatch-home.html#fig04-10)).

---

![](assets/fig04-10_fragment_match_screen.png "Figure 10. Fragment matching options. Select a feature of interest and click the 'Search' button.")

Figure 10. Fragment matching options. Select a feature of interest and click the âSearchâ button.

---

Fragments measured within the feature of interest will be matched against database fragments with known annotations. Complicated spectra may take a moment but generally completes within 30 seconds yielding a variety of results to indicate possible compound identity. Results are presented as an annotated mass spectral uncertainty plot ([Figure 11 left](msmatch-home.html#fig04-11)) and additional information about measured spectra are provided in an expanding table ([Figure 11 right](msmatch-home.html#fig04-11)).

---

![](assets/fig04-11_fragment_match_spectra.png "Figure 11. Graphical display of fragment annotations on an uncertainty mass spectral plot and the measured data provided to MSMatch.")

Figure 11. Graphical display of fragment annotations on an uncertainty mass spectral plot and the measured data provided to MSMatch.

---

Matched fragment annotations and associated metadata are provided below this output ([Figure 12](msmatch-home.html#fig04-12)). Match records are located in the expandable table to the left. As matches may have structural annotation or not, these are separated to indicate confidence and annotations with structural notation are displayed at the top. Select a row in the table (the top record is selected by default) to update the following displays.

* A human readable measurement narrative about the known fragment.
* If structural notation is present a molecular model is displayed (requires rdkit to be active in the API server)
* Compounds and peaks within which this fragment has been previously annotated appear in the table to the right. Select the tab to switch between compounds and peaks.

---

![](assets/fig04-12_fragment_match_results.png "Figure 12. Results from matching user provided data to annotated fragments with associated metadata. Selecting a row in the left-hand table will update data to the right in real time. Inset A: click a button to save that tableâs results. Inset B: an example of peak information available.")

Figure 12. Results from matching user provided data to annotated fragments with associated metadata. Selecting a row in the left-hand table will update data to the right in real time. Inset A: click a button to save that tableâs results. Inset B: an example of peak information available.

---

Two options are available for more contextual information regarding compounds and peaks.

* Click **More Compound Information** to list other known or generated aliases for a compound and provides links to those resources if available. These aliases have either been collated from existing locations or, in the case of most machine-readable identifiers, generated using rdkit.

---

![](assets/fig04-13_additional_compound_info.png "Figure 13. Additional information available for compounds.")

Figure 13. Additional information available for compounds.

---

* Click **More Peak Information** to provide a human readable narrative regarding measurement methods and sample information provided as part of the database accession process. Narratives are constructed directly from the underlying linked data tables by the database and stored as a database view.

---

![](assets/fig04-14_additional_peak_info.png "Figure 14. Additional information available for peaks.")

Figure 14. Additional information available for peaks.

---

#### Step 5. Closing Down

When finished using the application, typing the escape key at the R console is the simplest way to stop the server and exit the application. If using RStudio there is a âstop signâ button at the top right of the console pane that will also stop it. When finished completely with the project, users also need to shut down the API server.

* Loading the entire project from the compliance script (i.e.Â MSMatch was launched using `start_app("msmatch")`) provides additional actions and includes a live database connection with the ability to read data into tables and preserve them for further analysis. Use the function [`close_up_shop()`](appendix-function-reference.html#fn_def_close_up_shop) with the argument `back_up_connected_tbls` set to `TRUE` to preserve these, or the default FALSE to simply close all connections including the API server).
* If launching the app directly and using the default settings there will be a session object named `plumber_service` connected to that server. To stop it, use the [`api_stop`](appendix-function-reference.html#fn_def_api_stop) function from the console or stop the service directly using `plumber_service$kill()`; it will also generally stop when the calling R process closes (e.g.Â when RStudio is closed), but it is highly recommended to stop it manually to prevent hanging connections.
* After closing all connections, a hanging connection may be indicated by the presence of â-shmâ and â-walâ files in the project directory. Flushing these hanging connections is not required but is recommended.
  + If launching MSMatch with the compliance script, run [`close_up_shop()`](appendix-function-reference.html#fn_def_close_up_shop) again.
  + Otherwise flush those connections by directly connecting and disconnecting with the DBI package:

    ```
    con <- DBI::dbConnect(RSQLite()::SQLite, "nist_pfas_nta_dev.sqlite")
    DBI::dbDisconnect(con)
    ```

Feature requests, suggestions, and bug reports are most conveniently submitted as issues via GitHub but may also be submitted by contacting the authors. New functionality suggestions are encouraged as the project tooling develops. Likewise, if the functionality demonstrated here is of interest to projects outside of PFAS, this is only one example implementation of the underlying technology stack (i.e.Â DIMSpec); contact the authors to see if your mass spectrometry data would be amenable to that framework as other implementation suggestions are encouraged and a larger goal of the project is to cohesively manage mass spectrometry data for non-targeted analysis within the Chemical Sciences Division and external stakeholders alike.

This concludes the User Guide for the Mass Spectral Match (MSMatch) web application. The following section contains technical details about the implementation and user customization of this digital assistant.