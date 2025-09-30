[![[skip navigation]](/Images/dot_t.gif "skip navigation")](#start)







## NIST Atomic Spectra Database Help Page

**General Information**
:   Introduction to the [ASD database](/PhysRefData/ASD/Html/contents.html)
:   Introduction to [Atomic Spectroscopy](https://physics.nist.gov/Pubs/AtSpec/index.html)
:   [List of Holdings](#HOLDINGS)
:   [ASD Data](#DATA)
:   [Navigation](#NAVIGATION)
:   [Searching for Data](#SEARCH_FORMS)
:   [Options for Viewing Data](#VIEWDATA)
:   [Using WWW Browser Features](#BROWSERS)
:   [Special Configuration and Term Notations for ASCII Output Files](#ASCIICT)
:   [Locating references in the ASD Bibliography](#VIEWREFS)

**[Spectral Lines](/PhysRefData/ASD/Html/lineshelp.html)**
:   [Lines Search Form](/PhysRefData/ASD/Html/lineshelp.html#LINES_FORM)
:   [Wavelength ordered searches](/PhysRefData/ASD/Html/lineshelp.html#WAVELENGTH_ORD) (including examples)
:   [Multiplet ordered searches](/PhysRefData/ASD/Html/lineshelp.html#MULTIPLET_ORD) (including an example)
:   [Selecting Spectra for Lines Searches](/PhysRefData/ASD/Html/lineshelp.html#LINES_SPECTRA) (including examples of spectral notation)
:   Setting Options for Lines Searches
:   [Setting Output Preferences](/PhysRefData/ASD/Html/lineshelp.html#LINE_OUTPUT_OPTS)
:   [Setting Additional Criteria](/PhysRefData/ASD/Html/lineshelp.html#LINE_CRITERIA)
:   [Output for Lines](/PhysRefData/ASD/Html/lineshelp.html#OUTPUT_LINE) (description of columns of output)

[Energy Levels](levelshelp.html)
:   [Energy Levels Search Form](/PhysRefData/ASD/Html/levelshelp.html#LEVELS_FORM)
:   [Selecting Spectrum for Levels Searches](/PhysRefData/ASD/Html/levelshelp.html#LEVELS_SPECTRUM)
:   [Setting Additional Criteria](/PhysRefData/ASD/Html/levelshelp.html#LEVEL_CRITERIA)
:   [Output for Levels](/PhysRefData/ASD/Html/levelshelp.html#LEVELS_OUTPUT) (description of columns of output)

[Ground States and Ionization Energies (GSIE)](iehelp.html)
:   [GSIE Search Form](/PhysRefData/ASD/Html/iehelp.html#IE_FORM)
:   [Selecting Spectra for GSIE Searches](/PhysRefData/ASD/Html/iehelp.html#IE_SPECTRA)
:   [Output for GSIE](/PhysRefData/ASD/Html/iehelp.html#IE_OUTPUT) (description of columns of output)

[Interface for Laser-Induced Breakdown Spectroscopy (LIBS)](libshelp.html)
:   [LIBS Input Form](/PhysRefData/ASD/Html/libshelp.html#LIBS_FORM)
:   [Output for LIBS](/PhysRefData/ASD/Html/libshelp.html#LIBS_OUTPUT)

---

Two lists of holdings are available. One for lines data, the other for levels
data. Either of these lists may be accessed by selecting "List of
Spectra" in the menu bar and then selecting the appropriate "List of
Holdings" link.

---

The List of Holdings for lines is arranged as a periodic table. Each element
symbol for which there are spectral lines in ASD is a link to the holdings data table
showing the following pieces of information for each stage of ionization:

* Total number of spectral lines.
* Number of lines with transition probabilities.
* Number of lines with level designations.

Each spectrum name in the table is a link to the complete list of lines of this spectrum in ASD.
The total number of included spectral lines for all spectra of the selected element is shown at
the bottom of the table.

In addition to the periodic table, the Holdings page provides a triangular diagram
filled with colored square boxes numbered according to nuclear charge growing from top to bottom
and ionization degree growing from left to right. Hovering the mouse over a box invokes a pop-up
indicator with the spectrum name and the number of included spectral lines for this spectrum.
Clicking on a square box invokes an output page of spectral lines for the corresponding spectrum.

---

The List of Holdings for levels is arranged as a periodic table. Each element
symbol for which there are energy levels in ASD is a link to the holdings data table
showing the number of energy levels in ASD for each stage of ionization.
Each spectrum name in the table is a link to the complete list of energy levels of this spectrum in ASD.
The total number of included energy levels for all spectra of the selected element is shown at
the bottom of the table.

In addition to the periodic table, the Holdings page provides a triangular diagram
filled with colored square boxes numbered according to nuclear charge growing from top to bottom
and ionization degree growing from left to right. Hovering the mouse over a box invokes a pop-up
indicator with the spectrum name and the number of energy levels for this spectrum.
Clicking on a square box invokes an output page of energy levels for the corresponding spectrum.

---

### I. What Data Sources are included in ASD?

Our basic policy is to include in ASD only those atomic data that have been
critically evaluated by NIST. The main exceptions to this are the energy level
data compiled by R.L. Kelly. His data are included in ASD for a few
spectra. While the Kelly energy level lists are unpublished, many of the data contained
in them are included in his lines compilations, which have been published in
the Journal of Physical and Chemical Reference Data, under the auspices of NIST
(formerly NBS) and AIP. Still, they have not been critically evaluated by NIST,
and a disclaimer to this effect appears when energy level data for these
spectra are queried in ASD.

The advantage of this NIST-evaluated-only policy is that it affords a set of
quality reference data. The disadvantage is that critical compilations
inevitably lag behind the generation of new data. Hopefully, computerized
handling of electronic data will cut this lag substantially in the future,
but the increasing amounts of data and decreasing number of personnel are
likely to ensure that the lag will remain significant.

We note that the large majority of the older data has held up well in
comparisons with newer results, at least in the sense that the original
estimated accuracies have generally proven to be representative.

If you have reason to believe that any ASD value is incorrect, please send your
comments via E-mail to [Feedback](/cdn-cgi/l/email-protection#5e2e3332733a3f2a3f73293b3c333f2d2a3b2c1e30372d2a70393128).
It would be helpful if the message included a copy of all the text contained in
the URL for the specific search. Our apologies to authors who have produced new
and/or improved values that are not yet included in ASD because critical NIST
compilations have not been performed for that spectrum since publication of the
new data.

### II. Reasons for differences between NIST published and ASD values

There are several reasons why differences sometimes occur between quantities
published in NIST compilations and the NIST ASD database:

***Factors that can affect energy-level and transition data:***

1. Some values have been corrected or updated since publication. Also, some
   additional entries have been made since publication.
2. Differences can of course also result from errors, either in the originally
   published value or in the value given in ASD. If you have reason to believe
   that an ASD value is incorrect, please sent your comments via E-mail to
   [Feedback](/cdn-cgi/l/email-protection#9eeef3f2b3faffeaffb3e9fbfcf3ffedeafbecdef0f7edeab0f9f1e8). It would be helpful if
   the message included a copy of all the text contained in the URL for the
   specific search.

***Factors that can affect transition data only:***

1. The data integration process for lines takes data from the most recently
   compiled data source for each line. For example, only the transition
   probabilities themselves are taken from the published transition probability
   compilations. All the information for the lower and upper levels of each
   transition are taken from the most current NIST compilations of energy levels
   for the appropriate spectrum. The Ritz wavelengths are derived from these
   level energies. Even the transition probabilities themselves may differ from
   those in the older compilations, because the values from the most recent NIST
   compilations are used when available.
2. The user may request to display both the observed and Ritz wavelength,
   the latter being derived from the difference in level energies. Both observed
   and Ritz values are only available for spectra for which comprehensive line
   lists are included. For some spectra, only a single wavelength, observed or
   Ritz, is available. In such cases the other value will be blank in the output.
   When both the upper and lower level energies are available, the Ritz
   wavelength is available. If both the observed and Ritz wavelengths are
   available, the "Obs-Ritz" difference is also available and can be
   included in the output.
3. Small differences for wavelengths, *λ*, may also result from our uniform application of a) an
   algorithm for determining the *significant figures* in Ritz wavelengths,
   and b) the index of refraction in air. This can in turn result in small
   changes in the transition probabilities, which for electric-dipole-allowed
   transitions are proportional to *λ*−3, and oscillator
   strengths, which are proportional to *λ*−1.  
   Internally, the energy level and wavenumber data are stored in ASD in units of reciprocal cm
   (cm−1), and the wavelength data are stored in units of angstroms (Å),
   in "standard" air for wavenumbers between 5000 cm−1 and 50000 cm−1
   and in vacuum within this interval. In the ASD output, the most accurate representation of the levels data
   is obtained when the data are requested in the same units of cm−1. Conversion to other units (eV or Rydberg)
   is made using the latest [CODATA
   recommended conversion factors](https://physics.nist.gov/cuu/Constants/energy.html). Conversion of wavelengths from vacuum to air
   and vice versa is made by using the five-parameter (three-term) formula from
   E.R. Peck and K. Reeder, J. Opt. Soc. Am. **62**, 958 (1972) (see more about the air-to-vacuum conversion
   in the [Help for Output Wavelengths](lineshelp.html#AIR) section).
   Before ASD version 5.5 of October 2017, uncertainties of these conversion factors were not taken into account
   in the displayed data. Starting with v.5.5, these uncertainties are combined in quadrature with the
   uncertainties of the stored data, and the output quantities are rounded off according to the
   combined uncertainties. Thus, the accuracy of the output wavelength data is somewhat degraded when the
   air wavelengths are displayed.

---

The ASD home page provides links for the user to view the following:

* ASD Version History.
* Lines Search Form
* Levels Search Form
* Ground States and Ionization Energies for all atomic spectra.
* LIBS Interface
* Introduction to the ASD database
* List of Spectra
* NIST Atomic Spectra Bibliographic Databases
* Help

Except for the home page and LIBS Interface, all pages of the database contain a menu bar at the
top, which may be used to navigate to any portion of the database mentioned
above. For example, if the user is viewing the Levels Form and wishes to now
view the Lines Form, the words "Lines Form" in the menu bar may be
selected to access the Lines Form. If the user is viewing the Lines Form and
desires help, the word "Help" in the menu bar can be selected to
access the ASD Help page.

The ASD home page provides links for the user to access the
following home pages and databases:

* The NIST home page
* The Physical Measurement Laboratory home page
* The NIST Physical Reference Data home page, along with other products and services of the NIST Physical Measurement Laboratory.
* Atomic Spectroscopy Data Center. This page contains a link to
  other NIST Atomic Spectroscopy databases and spectral atlases.
* A database of NIST critical compilations on atomic spectra.
* NIST Standard Reference Data home page.

Most of these links to home pages, as well as the link to the ASD version history, are
only accessible from the ASD home page and not from within the database.

---

The ASD database provides three primary search forms for accessing
data. The [Lines Search Form](/PhysRefData/ASD/Html/lineshelp.html#LINES_FORM) (referred to
as the Lines Form) provides access
to transition data for atoms and atomic ions (referred to as lines data).
The [Energy Levels Search Form](/PhysRefData/ASD/Html/levelshelp.html#LEVELS_FORM) (referred to
as the Levels Form) provides access to
energy levels data for atoms and ions (referred to as levels data).
The [Ground States and Ionization Energies Search Form](/PhysRefData/ASD/Html/iehelp.html#IE_FORM)
provides access to data on ionization energies and total binding energies of atoms and atomic ions.

These forms require that the user fill in the spectrum/spectra of interest
(and for lines,optionally, the wavelength region of interest)
and then select the "Retrieve Data" button.
Access to output options
(e.g., selection of HTML tabular output or ASCII output) and additional search
criteria (e.g., selection of an energy bound) is provided.

The [Interface for Laser-Induced Breakdown Spectroscopy (LIBS)](/PhysRefData/ASD/Html/libshelp.html#LIBS_FORM)
provides a tool for building synthetic spectra of mixtures of chemical elements at typical LIBS plasma parameters and for
comparing the synthetic spectrum with an experimental one.

---

***Defaults for Viewing Data***

The ASD database provides the user with the option to view data as either an
HTML formatted table (which includes subscripts and superscripts) or as an
ASCII table. The default is to display the output as an HTML formatted table.

The ASD database provides the user with the option to view data either in its
entirety or in pages. The default is to display the output in its entirety,
i.e., as one output file that can be scrolled through.

By increasing the window size and decreasing the font size, it is possible to
view more data per screen.

***Viewing Data as an ASCII Table***

An advantage of viewing ASCII output is that it takes less time
to display ASCII output than formatted data. Another advantage is
that ASCII data may be downloaded into a spreadsheet or other program
located on the client computer.
Both the Lines Form and the Levels Form, have a section for
"Output Options."
Under the "Output Options" section, next to the "Format output"
heading, the pull down menu can be used to select "ASCII (TEXT)."

***Viewing Pages of Data***

An advantage of viewing data one page at a time is that the column headings
are displayed at the top of each page of data.
Another advantage is that viewing smaller amounts of data is much faster
than viewing a large file of data in its entirety. A disadvantage of viewing
data one page at a time is that it may be more convenient to scroll through
one large file of data instead of waiting for the browser to load the next or
previous page.

Each page of data includes the current page number, the total number of
pages, and links to view the next page of data or the previous page of data.
The page size can be customized to accommodate variance in font size and screen
size.

To change the default so that output is displayed in pages that can be viewed
one at a time, follow the steps listed below.

1. From either the Lines Form or the Levels Form, look for the section
   labeled "Output Options."
2. Under the "Output Options" section, next to the "Display output"
   heading, use the pull down menu to select "in pages."
3. The page size can be changed as needed.

***Viewing Large Amounts of Data***

The default is to display output as an HTML formatted table
in its entirety. There is a certain amount of overhead associated
with creating output containing a large number of lines of
data formatted as an HTML table. The speed with which search
results can be viewed by the user is a function of the following:

* the speed of the client computer,
* the amount of memory on the client computer,
* the amount of data,
* the number of columns of formatted output,
* the speed of the network, and
* the browser's ability to load and render formatted tables.

Note that in some cases, for searches returning a large amount of
output, some browsers may lock up or not
be able to display all the data correctly. If you have a problem
viewing a formatted table of data, choose one of the other display
options or limit the range of your search.

An advantage of displaying all lines of output as a formatted table is
that the user is able to view the formatted data in its entirety. Another
advantage is that the user can use the browser's "find" capability
to scroll down to a value of interest. The disadvantage is that this option
can be very slow. A considerable amount of time will need to be spent loading
the data into the browser, and having the browser determine how to render the
many columns of data.

Users with less capable systems, or users primarily interested in viewing the
first portion of the data, may opt to choose one of the following options:

1. Display 100 lines (maximum page size) as a formatted table.  
   Two advantages of this option are that it is faster than viewing the formatted
   data in its entirety and that the user is still able to view a large portion of
   the data (100 lines) at a time. Another advantage is that the user is able to
   see column headings displayed at the top of each page of data. The disadvantage
   is that the user is not able to view the data in its entirety.
2. Display 15 lines (or default page size) as a formatted table.  
   The advantages of this option are that it is relatively fast and that the user
   is able to view formatted data. Another advantage is that the user is able to
   see column headings displayed at the top of each page of data. The disadvantage
   is that the user must view pages of data one by one.
3. Display output as an ASCII table.  
   This option has the advantage that it is relatively fast. The browser does not
   need to load a large file containing formatted data and the browser does not
   need to spend time determining how to lay out the many columns of data. Another
   advantage is that the user can scroll through the data in its entirety. The
   disadvantage of this option is that the user is not able to view superscripts,
   subscripts, italics, etc. that can be viewed with formatted data.

---

***Downloading Data***

WWW browsers provide the capability for data to be downloaded and saved as a
local file. For downloading ASCII files, and/or for reading into
spreadsheets, we suggest the following procedure:

1. On the Lines or Levels Form, go to the section "Output Options";
2. Click the pulldown menu for "Format output" and choose "as ASCII
   (TEXT)";
3. Check the "No Javascript" checkbox in the Lines or Levels Form;
4. Retrieve database output;
5. Under "File," choose "Save as," assign the file a name,
   and save it;
6. In a text editor, remove any undesired headers from the saved ASCII
   output file, and
7. When reading the ASCII output file into spreadsheet software, specify the
   delimiter as a pipe, i.e., "|".

***Changing Fonts***

Font size effects the amount of data that can be viewed per screen;
a smaller font size allows more data to fit on each screen.

***Finding Specific Values in Output***

WWW browsers provide the capability to find specific words/patterns in
a page of output displayed. For example, using an HTML page of output
for Lines Data or Levels Data, if the user searches for "5/2"
then the browser will scroll down to the line of data containing the value
specified and highlight the value.

Because of the way data are formatted,
care must be taken when searching for values. Note the following examples.

1. To search for the configuration "2*s*22*p*2"
   * for ASCII output: Search for the phrase "2s2.2p2" (note that periods are
     inserted whenever necessary to avoid ambiguity due to the lack of superscripts).
     Angular brackets enclose *J* values of the parent terms.
   * HTML Table: Search for the phrase "2s22p2".
2. To search for the term "3D" note that it is easier to specify a case sensitive search.
3. To search for the term "2[5/2]":
   * ASCII output or HTML Table: Search for the phrase "2[5/2]".
4. To search for the *J* value "3/2,5/2":
   * ASCII output or HTML Table: Search for the phrase "3/2,5/2".
5. To search for the energy level "60333.43":
   * ASCII output: Search for "60333.43".
   * HTML Table: Search for "60 333.43".
6. To search for the energy level "87 789.63":
   * ASCII output: Search for "87789.63".
   * HTML Table: Search for "87 789.63"; note that
     searching for "87789" will not work. To search for all energy
     levels greater than 87000, search for "87 ".

***Printing Data***

Many WWW browsers offer the capability to print directly from the browser. An
alternative is to download the data and then print the data from the local
computer.

The database provides an option which allows a user to choose the columns of
data to display. Suppressing specific columns of data might be helpful for
printing purposes. Specifying landscape orientation and reducing the font size
will simplify the task of printing a large amount of data.

---


The number of equivalent electrons (occupation number for a particular
subshell) is given as a full-size integer following the electron symbol
(e.g. 4d5 represents 4*d*5). The symbols for different
subshells not separated by parent terms or spaces are separated by periods
(e.g. 4f3.5d.6s2 represents 4*f*35*d*6*s*2). The
multiplicity of a term is given immediately preceding the term symbol,
and an odd-parity term is indicated by an asterisk following
the term symbol (e.g. 3H\* represents
3H°). The parity of a level
having no term name is also indicated by the presence (odd parity) or absence
(even parity) of an asterisk in the "Term" column. The *J* value
of a level given with a configuration designation appears within "< >"
brackets following the term symbol (e.g. 2s2.2p4.(3P<2>).3d 
represents
2*s*22*p*4(3P2)3*d*
and 3p5.(2P\*<3/2>).5g represents
3*p*5(2P°3/2)5*g*).

---

The bibliographic references given in ASD are HTML links to complete
bibliographic records stored in the NIST Atomic Spectra Bibliographic
Databases. ASD is integrated with two of these Databases, *Atomic Energy
Levels and Spectra Bibliographic Database* and *Atomic Transition
Probability Bibliographic Database*. The complete bibliographic records
are displayed in a separate new window and contain, where available, HTML
links to online journal pages hosting the articles. If the user has a
subscription to the online journal, it is possible to download the full-text
article from the journal.

---