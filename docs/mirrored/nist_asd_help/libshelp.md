[![[skip navigation]](/Images/dot_t.gif "skip navigation")](#start)







[![Go to top of ASD Help](/Images/top.gif "Go to top of ASD Help")](/PhysRefData/ASD/Html/help.html) The ASD interface for Laser-Induced Breakdown Spectroscopy (LIBS) provides a
convenient and straightforward access to the ASD data of relevance to LIBS
applications, allowing the users to plot synthetic spectra of virtually any
mixture of chemical elements at typical physical conditions of laser-induced
plasmas and compare these synthetic plots with experimental spectra.

In this interface, one can specify a plasma composition and rough initial
estimates of observational parameters, such as electron temperature and
density, wavelength range, and spectral resolution. Initial Saha-Boltzmann
modeling is made on the server side, and all relevant data, such as spectral
lines and energy levels data, are transmitted to the user's computer, which
plots the simulated spectrum. Then it is possible for the user to change the
appearance of the plot by zooming in and out or selecting graphs for
individual species and recalculate the simulated spectrum with modified
parameters. In addition, the user can load an experimental spectrum into the
same plot and compare it with the simulation. In the current version
first released in June 2017, fitting of the experimental spectrum can only
be made manually, by changing the temperature, density, resolution, or
element concentrations.

For explanations how the LIBS modeling is done in ASD, please read the section
on [Saha-LTE plots](lineshelp.html#LINES_INP_SAHA_PLOT) that can be
produced with graphical options in the Lines form of ASD. The LIBS modeling
uses the same procedures as Saha-LTE plots for calculation of ion abundances,
level populations, and line intensities. LIBS graphical and modeling options are more flexible
than those of Saha-LTE plots; however, the latter have some functionality that
is missing in LIBS. For example, the LIBS interface does not allow the user to
choose any particular isotope of a chemical element, while Saha-LTE does.
Also, for the spectra of hydrogen and deuterium (H and D), Saha-LTE plots can be made
for a high-resolution spectrum that resolves the fine structure, while LIBS plots
can only be made for a low-resolution configuration-averaged spectrum of H
(but not D).

---



## [Go to top of page](#Top)   LIBS Input Form

This input form allows the user to specify the chemical composition of the
plasma, its temperature and density, the range of observed wavelengths, and
the spectral resolution desired for the synthetic spectrum.

At a minimum, the user must enter at least one chemical element
and then click "Retrieve Data".

The LIBS Input Form prompts the user for the following information:

---

In the **Element** box, type the **element symbol**, which is a standard symbol of a chemical element, according to
 [NIST Periodic Table of the Elements](https://www.nist.gov/pml/periodic-table-elements).

The LIBS modeling requires data on spectral lines for the first three spectra of an element (neutral, singly ionized, and
doubly ionized), including the energy-level classifications and radiative transition probabilities. For most elements of
common interest for LIBS, ASD has sufficiently large data sets including this information. However, there are many
exceptions. Thus, before starting the modeling, it is a good idea to check the [Lines Holdings](/cgi-bin/ASD/lines_pt.pl)
to ensure that the data coverage in ASD is sufficient for the elements of interest.

In the **Percentage** box, if more than one element is present, type the percentage of this element in the mixture
(i.e., the percentage of the number of atoms of this element) and hit the [Tab] or [Enter] key. Initially, the form
displays only one input box for an element and one for its percentage. If the entered percentage is less than 100, an additional
pair of boxes will appear, allowing the user to enter the second element and its percentage. This appearance of new boxes
will continue until the sum of entered percentages is equal to 100. The user can edit the previously entered elements and
their percentages or remove a particular element (except the first one) by clicking on a [Remove]
link before its box. In this case, the other percentages may be automatically recalculated, so that they sum up to 100, or
a prompt for an additional element may appear. It is possible to enter an element with a zero percentage. Such an element
will not contribute to the initial modeling performed by the ASD server. However, its relevant line and level data will be
submitted to the user's computer, where subsequent modifications can be made to the percentage composition and other
parameters (see Help for the [Recalculate Form](#LIBSOUTFORM) appearing in the output.

The wavelength range limits must both be non-empty. They must be valid non-negative numbers, and the **Upper Wavelength** must be
greater than the **Lower wavelength**. Pay attention to the **Wavelength Units** and the [**Wavelength in**](#LIBS_WAVIN)
choices, as they cannot be modified in the [Recalculate Form](#LIBSOUTFORM).
In the LIBS output, the wavelengths can be presented in one of the two standard ways,

* In standard air in the range between 200 nm and 2000 nm and in vacuum outside of this range, or
* All wavelengths in vacuum.

The choice is made by selecting a corresponding radio button next to the **Wavelength in** label in the form.

Wavelengths of all spectral lines displayed in the LIBS output are the Ritz wavelengths, i.e., the wavelengths calculated from the energy levels
(see Help on [Observed and Ritz Wavelengths](/PhysRefData/ASD/Html/lineshelp.html#OUTWAVELENGTH) for more
explanations, including the conversion between the air and vacuum wavelengths).

To avoid having a complicated code that would automatically change the values in the input boxes following a possible
change of the wavelength units, we adopted to use the *resolving power* instead of *wavelength resolution*.
Thus, in the **Resolution** input box, the user is expected to enter the dimensionless value of the resolving power
equal to the ratio of the wavelength to the full line width at half-maximum. The resolution is assumed to be constant in the
entire wavelength range.
In the present version of the LIBS software, there are three advanced input options: the maximum ion charge, the minimum
relative line intensity, and the choice for the intensity scale. These options are hidden by default, but can be displayed
by clicking on the "Advanced Options" button.

The default option for maximum ion charge is '2+', meaning that only the spectra of neutral atoms, singly- and
doubly-charged ions will be displayed in the LIBS plots. The user can select the values '3+', '4+', and 'no limit' from the drop-down
list in the Advanced Options section. The last option means that there will be no limitation on the ion charge, except for the
presence of lines of these ions in the selected wavelength range. Note that LIBS plots can use only those lines from the ASD data
sets that have non-empty transition probability values.

The minimum relative intensity (default 0.01) is used to limit the selection of lines displayed in the LIBS plots to those
having possible relative intensities within the given wavelength range not less than the given threshold value. Rough estimates of
relative intensities are hardcoded in the ASD database. They have been calculated as maximum possible values in a reasonable
range of electron temperatures (from 0.05 to 2 times the ionization energy of a given ion). When a LIBS query is executed, these
relative intensities are renormalized for the wavelength range specified by the user. It should be kept in mind that, although
LIBS plots allow the user to zoom in on small wavelength intervals (with a possible purpose of displaying weaker lines), the
lines omitted in the initial query still cannot be displayed. To display those weak lines, the user must go back to the LIBS
input form and select a narrower wavelength range and/or a lower value of the allowed minimum relative intensity. A zero value
of the minimum intensity available in the drop-down list effectively removes this limitation on the number of lines, but the
queries may become prohibitively slow for spectra having large numbers of lines.

The plasma emission intensities are calculated in arbitrary units. These units can be chosen from one of the two options:
1) energy flux units (the default choice) or 2) photon count units. For a more detailed explanations how the spectrum intensities
are calculated in the LIBS modeling, please read the Help page on [Saha-LTE plots](lineshelp.html#LINES_INP_SAHA_PLOT) of the
ASD Lines section.

---



## [Go to top of page](#Top)   LIBS Output

The LIBS output consists of several interactive elements:

---

The plot displays a synthetic spectrum calculated for the given mixture of chemical
elements and plasma parameters (electron temperature and density) assuming the
Saha-Boltzmann equilibrium and a constant (user-defined) spectral resolving power.
The constant resolving power is equivalent to the assumption that the line shapes
are entirely defined by Doppler broadening with a certain temperature. Thus,
we refer to this plot as a **Doppler-broadened plot**. Alternatively, the
user can choose to view a **stick plot** displaying vertical lines at the exact
positions of all spectral lines involved, with heights defined by the calculated intensities.

The plots are drawn using the
[Google Line Charts](https://developers.google.com/chart/interactive/docs/gallery/linechart)
technology. They have many interactive features, such as tooltip pop-up boxes with
information about data points (appearing when mouse is hovered over the lines in the plot)
and legends on the right side that can be clicked on to highlight a particular curve.

Depending on the screen size and resolution, the plot appears on the right side or
below the [Recalculate Form](#LIBSOUTFORM) and the plot-control box,
which are always shown on the left side at the top of the output window.

The legend on the right side of the plot lists the displayed spectra and shows
relative concentrations of the corresponding ions for the given element abundances,
electron temperature, and density.

The horizontal axis of the plot contains wavelengths in the units selected in
the [LIBS Input Form](#LIBS_FORM). If the **stick plot** is selected, the
axis title is "Ritz wavelength" to reflect the nature of the displayed
wavelengths. For a **Doppler-broadened plot**, the axis title is "Wavelength,"
since the displayed curves are calculated on a finite-step grid defined by the given
[Resolution](#LIBSOUTRES). However, all underlying calculations are made
with the same Ritz wavelengths as displayed in the stick plot.

The vertical axis contains the calculated line intensities in arbitrary units.
Its scale is automatically adjusted when the user [zooms in](#LIBSOUTZOOM)
on a particular wavelength region.

To zoom in on a particular wavelength region, left-click with the mouse on the left side of the desired region
of the plot and, while holding the left mouse button down, drag to the right side of the region, then release the mouse.
To pan (i.e., return to the original view), right-click anywhere on the plot.
To display a stick plot instead of a Doppler-broadened spectrum, check the checkbox on the
left side of the "Show stick plot" label in the plot-control box below the
"Recalculate" button.

The number of the displayed spectra decreases in the stick plot, as the
"Sum" plot cannot be calculated in this mode. Consequently, the
automatically-assigned colors of data points belonging to different spectra change compared to the
Doppler-broadened spectrum.

To return back to the Doppler-broadened spectrum plot, uncheck the "Show stick plot" checkbox.

The user can select one or more of the available spectra by using the "Select data to display" list in the
plot-control box below the "Recalculate" button. To select one spectrum, click (with the mouse) on its name in the list.
To select multiple spectra, press and hold the [Ctrl] key on the keyboard before clicking on each spectrum name or press and hold the
[Shift] key before clicking on the first and last of the consecutive spectra in the list. Then release the keys.
Below the plot, next to the "View Data Source" label, there are three buttons allowing the user to
view the spectral-line data in one of the three formats: ASCII, CSV, and HTML. Clicking on one of these buttons
will invoke a new window (or a new tab, depending on the browser settings) showing a table with multiple columns.
The first column contains the wavelengths (Ritz wavelengths for a stick plot or the wavelength-grid points for
a Doppler-broadened spectrum). All the other columns contain the calculated intensities, separately for each
spectrum in the plot. For a Doppler-broadened spectrum, the first column next to the wavelengths, labeled "Sum(calc),"
is the total spectrum calculated as a sum of the spectra of all atoms and ions in the mixture.
If a [User Spectrum File](#LIBSOUTUSERSP) is
uploaded to the plot, it is assumed to be an experimental spectrum, and a column labeled "Exp(user)" containing this
spectrum data is inserted before the "Sum(calc)" column. In addition, a column labeled "Residual" is
appended on the right. It contains the differences of experimental (from the user file) and calculated intensities.
Clicking on the button "Display PNG" below the plot invokes an image of the plot (in a portable graphics format)
displayed in a separate browser window. The image can be saved or printed on the user's computer by using the browser controls.
A user spectrum file can be loaded to the plot by clicking on the "Select User Spectrum File" button below the
plot-control box. As noted the [introduction](#start), no user data are transmitted anywhere outside the
user's computer. All manipulations with the plot are made locally on the user's computer. Connection to the Internet is
still required, because the Javascript code drawing the plot is located on Google Chart servers.

The user spectrum file must be an ASCII file in the usual format: two columns of numbers delimited by space. The first column
is the wavelength, and the second is the observed intensity in arbitrary units. A sample user file can be viewed by clicking on the
question mark on the right side of the button. The file may contain column headings or any other description information on the
first line. The first line will be ignored by the LIBS code, if it cannot be interpreted as two numbers delimited by space. No blank
lines are allowed in the middle or at the end of the user file.

When the user file gets loaded in the plot, the observed intensities are automatically normalized to match the scale of the
calculated spectrum. The sum of residuals (observed minus calculated intensities) will be displayed inside the [Recalculate Form](#LIBSOUTFORM), which can be useful in modeling: the user can minimize the sum of residuals by varying the plasma
parameters.

If the wavelength range in the user file is narrower than in the initially calculated spectrum, the wavelength range of the
plot will be reduced to match that of the user spectrum. This may cause some of the calculated spectra to be dropped from the
plot, if all their lines were outside the user spectrum range.

## [Go to top of page](#Top)  The Recalculate Form

The Form allows the user to modify the following parameters:

* Electron temperature (*T*e)
* Electron density (*N*e)
* [Resolution](#LIBSOUTRES)
* Element percentages

The user should click the "Recalculate" button to redraw the plot with the modified parameters.

### [Go to top of page](#Top)  Changing the wavelength resolution

As in the [LIBS Input Form](#LIBS_FORM), the "Resolution" in the "Recalculate" Form means the
dimensionless resolving power, i.e. the ratio of the wavelength to the full line width at half-maximum.
The resolution is assumed to be constant in the entire wavelength range. When the initial plot is built
by the NIST ASD server, there is a limitation on the maximum allowed resolution, which
depends on the number of spectral lines involved in the user request. If the requested resolution exceeds
the allowed limit, it will be automatically decreased to the maximum allowed value, and a warning about it
will be displayed in fine print at the top of output page. This does not prevent the user from setting a
higher Resolution in the "Recalculate" Form, because the limitation on the number of
points in the wavelength grid on the user's computer is usually much milder. It is defined by the memory
size accessible by the browser. High-resolution plots may work slower.

## [Go to top of ASD Help](/PhysRefData/ASD/Html/help.html)  ASD Data Table Output Link

This link is displayed at the very bottom of the output page. Clicking on it invokes a Lines output page of ASD listing detailed information
about all the spectral lines involved in building the calculated spectrum.

---