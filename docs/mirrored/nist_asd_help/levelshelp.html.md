[![[skip navigation]](/Images/dot_t.gif "skip navigation")](#start)







[![Go to top of ASD Help](/Images/top.gif "Go to top of ASD Help")](/PhysRefData/ASD/Html/help.html) 
The ASD database provides energy level data for atoms and ions. For more
information consult [Introduction to and Contents of the ASD](/PhysRefData/ASD/Html/contents.html).

---



## Energy Levels Search Form

The ASD Levels Search Form, referred to as the Levels Form, provides access to
the energy level data. Submitting the Levels with information specified by the user
generates a level list for a specified spectrum.

At a minimum, the user must enter a
[spectrum](#LEVELS_SPECTRUM) of interest (e.g., Fe I)
and then click "Retrieve Data".

The Levels Form prompts the user for the following information:

* [Spectrum](#LEVELS_SPECTRUM) of interest (e.g., Fe I).
* Energy level units (selected from the pulldown menu).
    
  Energy levels may be displayed in one of the following units:
  + cm−1 (reciprocal centimeter or wavenumber), the default unit
  + eV (electron Volt)
  + Rydberg
  + Hartree (=2×Rydberg)
  + GHz
* Choice of viewing the output as an HTML table, ASCII table, a [CSV or tab-delimited data file](#CSV)
  (selected from the pulldown menu).
* Choice of viewing (scrollable) data all at once, or one page at a time (selected from the pulldown menu).
* Page size.
* Choice of energy ordering of the output, i.e., term ordered or energy ordered.
* Choice of the output information for levels.
* Choice of the output of the relevant available bibliographic references.  
  For most ions, bibliographic references are available and can be
  retrieved by selecting the "Bibliographic references" checkbox.
* Choice of the output of the level splitting, i.e., the difference between
  two adjacent energy levels (different levels may be "adjacent" with different ordering of output).
* Electron temperature ***Te*** for calculation of partition function.

For levels output, the default is to display the following data:

* Principal Configuration
* Principal Term
* Level
* Uncertainty
* *J*
* Landé *g-factor*
* Leading Percentages
* Bibliographic References

To suppress display of any of the information listed above, the corresponding
checkbox can be unclicked.

[Additional search criteria](#LEVEL_CRITERIA) are available for all
ions and can be reached by pressing the "Set Additional Criteria" button.  

---



## [Go to top of page](#Top)   Selecting a Spectrum for Levels Searches

To specify an element on the Levels Form, simply enter the chemical symbol for
the element (e.g., Fe or fe). To indicate a particular
spectrum (ionization stage), enter (after a space) either a Roman numeral or an Arabic numeral
after the element symbol (NOTE: Fe I = Fe0+,
Fe II = Fe1+, etc.). Alternatively, a
spectrum may be specified by the name of its isoelectronic sequence (e.g.,
Si Li-like = Si XII,
Si Na-like = Si IV).
The user can also specify a particular isotope by
including an atomic mass number before the element symbol, e.g., 198Hg I.
Isotopes of hydrogen can also be specified by using their alternate element symbols,
D I or T I. The symbol H I will produce
the same results as 1H I.
For levels searches, output can only
be generated for one spectrum at a time.

#### *Examples of Spectrum Notation*

|  |  |
| --- | --- |
| **To specify** | **Enter** |
| Neutral sodium | Na I |
| Neutral sodium | Na 0 |
| Neutral iron | fe i |
| Lithium-like magnesium | Mg x |
| Lithium-like magnesium | mg Li-like |
| Singly-ionized 11B | 11B II |

---



## [Go to top of page](#Top)   Setting Additional Criteria (from the Levels Form)

Clicking the "Set Additional Criteria" button on the Levels Form
causes a list of additional search criteria to be displayed. These options are
set to default values. Therefore, it is not mandatory that the options be set
before using the database.

Before selecting the button "Set Additional Criteria," the user must
specify a spectrum on the Levels Form.

The following search criteria may be specified:

* Upper bound of energy (in the energy units selected on the Levels Form).
* Parity. The default is to retrieve levels of both parities. The user may specify either odd or even parity.
* Configuration. The search criteria are used to create a list of
  possible configurations for the chosen. The default is that no configuration
  bound is specified. The pulldown menu can be used to select a configuration bound of
  interest. Alternatively, the text box can be used to type in the initial or ending
  portion of a configuration of interest.
* term. The search criteria are used to create a list of possible
  configurations for the chosen ion. The default is that no term bound is
  specified. The pulldown menu can be used to select a term bound of interest.
  Alternatively, the text box can be used to type the initial or ending
  portion of a term of interest.
* *J* value

If the spectrum on the Levels Form is changed, then clicking on the
"Update Criteria" button on the Levels Form will update the list of
additional search criteria.

---



## [Go to top of page](#Top)   Output for Levels (by table column heading)

---

For most of the headings, we discuss separately the cases of levels tabulated
with and without leading percentages.  
  


#### *Levels Tabulated With Leading Percentages*

The electronic configuration for the largest component in the calculated
eigenvector for the level is normally given in this column. (The configuration
is for the largest component to within the estimated uncertainty of the
calculation; see "[Term](#LOUTTERM).") Any ancestor terms
or *J* values appropriate to this component are normally included with the
configuration, as in the examples in the
[Introduction to Atomic Spectroscopy](https://www.nist.gov/pml/atomic-spectroscopy-different-coupling-schemes).

A question mark "?" after the configuration indicates that the
assignment of the observed level to the calculated eigenvector is uncertain.
This particular notation for an uncertain assignment usually implies that at
least one other plausible assignment of the level would give a different
configuration or set of parent terms for the leading component.

The configuration is listed only once for a set of levels grouped into a term.
All notations given with the configuration, including any question marks, apply
to each level of such a term.

In cases of strong configuration interaction, more than half the percentage
composition of a level may be due to components from a configuration different
from that for the leading component; such an example makes it clear that the
configuration given in the first column does not necessarily represent a
configuration assignment of the level. A particular configuration may appear in
the first column for more levels than the pure configuration is allowed.
In such cases of strong configuration interaction, the label used in the
Configuration column may correspond not to the largest,
but to a minor component of the eigenvector composition. For such heavily
mixed levels, the configuration label has little or no physical meaning and is
used in the database for bookkeeping purposes only. The configuration labels
of such mixed levels are usually assigned so as to
satisfy the requirement of uniqueness of the combination of the combination
of the configuration, term, and *J* values for each level.

#### *Levels Tabulated Without Leading Percentages*

The reliability and indeed the meaning of configuration assignments made
without supporting calculations vary greatly. Even in the most complex spectra,
there may be some levels or groups of levels belonging largely to a single
configuration. The observed structure, magnetic *g* values, intensities,
isotope shifts, and other data can in such cases lead to unambiguous assignments representing
high purity. (Examples are the lower levels of most
4*f N*6*s*2,
4*f N*6*s*,
and 4*f N* configurations in the rare earths.)
Quite often, however, the levels to be interpreted comprise a dense structure
to which several configurations are known or expected to contribute. Some
preliminary configuration assignments may be possible and useful in such cases,
but such assignments for the bulk of the levels are often best regarded as
tentative until confirmed by calculations. In many cases, meaningful
single-configuration assignments do not exist.

We have tried to indicate doubtful features of the interpretations in the
discussions of particular spectra in our compilations and, to some extent, in
the tables. A question mark following the configuration indicates explicitly
that the assignment is doubtful. A doubtful ancestor term is indicated by a
question mark after the term symbol within parentheses.

In some cases, the configuration for a level may be known, although the
appropriate ancestor terms (or even the preferred order of coupling of the
electrons) cannot be determined without calculations. Such a configuration
assignment (together with the final term and *J* value) without full
ancestry does not in general serve as a unique name for the level.

#### *Limits*

The wavenumber corresponding to the principal ionization energy is entered
in proper sequence under "Level." The corresponding entry in the
first column is the symbol for the next higher spectrum of the element,
followed by the configuration and term designations and the *J* value for the ground level of
this next ion. The word "Limit" appears in the "Term" column (the levels of the
higher ion being limits for series in the lower spectrum). If the known levels
of the lower ion (or atom) extend above the principal limit, one or more of the
higher limits are also given at appropriate positions.

## [Go to top of page](#Top)  Term

#### *Naming of Levels, Grouping of Levels into Terms, Other Conventions*

A term symbol in the second column belongs to the eigenvector component whose
configuration and ancestry appear in the first column. The assignment of a set
of levels to a term is indicated by grouping the levels and by listing the
configuration and term symbol for only the first (lowest) level of the group.
The presence of both a configuration with all necessary ancestor terms in the
first column and a term symbol in the second column guarantees that each of the
levels grouped with the term is uniquely designated by the symbols in the first
two columns, together with the *J* value; i.e., such levels have names.
This naming convention also applies to isolated levels not grouped into terms.
The use of the (*J*l, *J*2) [term symbols](https://www.nist.gov/pml/atomic-spectroscopy-different-coupling-schemes) in this connection
should be noticed; a *J*1,*J*2 configuration
notation in the first column is indicated as a name for the associated level(s)
only if a (*J*1, *J*2) symbol appears in the
second column.

In our various NIST compilations we have not followed a single set of
guidelines in retaining or forming terms (by grouping levels). Probably the
strictest criteria were applied to the rare-earth spectra, where we usually
retained or formed a term if half or more of the candidate levels for the term
were known and had leading components approximately 45 % or larger. The 45 %
requirement was sometimes lowered significantly for levels having leading
components sufficiently larger than the corresponding second components.
Additional levels of lower purity (~30 % to 45 %) were retained (or assigned) to
help complete a multilevel term provided certain conditions were met. Thus the
component for an assigned term name is normally the leading component in the
eigenvector, and is also as large a percentage of the particular name as occurs
in the eigenvector of any other level (known or not) with the same *J*
value. We also tried to avoid a name for which the configuration contributes
less to the total composition of the level than some other configuration. These
are minimal requirements for avoiding completely inappropriate names.

One can assure more generally satisfactory names by disallowing any name
representing significantly less than 50 % eigenvector purity; and in the case of
a leading percentage near 50 %, by requiring that the second percentage be
significantly smaller (alternate designation clearly less appropriate), and
that no other eigenvector should have a comparable leading percentage (~50 %)
for the same designation. The weaker criteria for the grouping and naming of
levels outlined above were adopted to allow practically any significant term
structure within a single configuration to be exhibited in the tables.

In cases of strong configuration interaction, it sometimes happens that
assignment to a particular term type remains appropriate for a level or level
group for which no meaningful configuration assignment is possible. Such term
names may usually be deduced by examination of the two leading eigenvector
percentages. In some cases of this type, we have entered the appropriate term
name under "Term," along with a letter indicating the situation (see,
for example, the "*y* 2D" term of
Al I).

Most of the calculated leading percentages for levels in question as to naming
are probably uncertain by several percent. In order to facilitate term
assignments, we have allowed a relatively few small deviations (by up to ~4 %)
from the above requirements on naming. These deviations are probably within the
uncertainties of the calculations.

Many of the resulting terms are incomplete, in the sense that no observed level
is listed for one or more of the possible *J* values of the term. A level
"missing" from such a term may not have been found in the analysis;
alternatively, it may be that no theoretical eigenvector is appropriate for the
corresponding designation, even under the relaxed criteria described above. The
first case is distinguished in the tables by printing the *J* value of the
level, and leaving a blank space in the "Level" column. The leading
percentages for such a missing level are given if available. In the second
case, the best candidate levels for the missing designation are usually known
and lie in the same region as the levels assigned to the term.

Levels belonging to a term most of whose levels have not been found may
nevertheless be grouped if the term appears to be an important one or lies in a
region where most terms are more complete. The printed *J* values of the
missing levels explicitly indicate possible extensions of the analysis. No
predicted term is shown. However, unless at least one level is known, and we
emphasize that missing predicted levels are generally *not* indicated in
these tables: no term symbols or *J* values are listed for missing levels
having low eigenvector purities or belonging to terms the levels of which are
not grouped (for whatever reason). The user is urged to consult the references
to published calculations for additional predicted levels.

A level with the leading percentage >45 % from a single-level term
(singlet, *S* term, etc.) is usually so named (shown as a term) if the
second percentage is significantly smaller, and if the other conditions
outlined above are met. Isolated levels (those remaining after the formation of
all terms) are named according to similar conditions.

Some levels of *f N* and
*dN* configurations have large eigenvector
components from two or more terms of the same *LS* type. Since the
resultant lowering of the purities has no physical significance, we have
retained the names of such levels having adequate total purity of a particular
*LS* type and labeled them with the Nielson-Koster index number for the
term of the leading component. (Of course, the corresponding group-theoretical
numbers have little meaning for such a low-purity term.) Similar considerations
have been applied in designating parent (or grandparent) terms arising from
*f N* configurations.

A question mark (?) after a term designation indicates that the assignment
of the observed level(s) to the calculated eigenvector(s) is uncertain.

## *J*: Total Electronic Angular-Momentum Quantum Number

The total angular momentum, *J*, is known for the vast preponderance of
energy levels. An uncertain *J* value for a level is usually known to
within two or three possible values; in such cases all the possible *J*
values, separated by *'or'*, are listed. Two or more comma-separated *J* values may be listed at a single
energy position to denote unresolved levels.

## [Go to top of page](#Top)  Level

The levels are normally given as they are stored in the database, in units of
cm−1, with respect to the ground level at zero cm−1.
In HTML output, odd-parity levels are shown in italics. The odd parity is also
indicated in the HTML output by a small circle symbol (°), or in the ASCII
output by an asterisk (\*) at the end of the term label.

Levels within terms are listed in order of position. Terms are listed in order
of lowest (known) levels, with ungrouped levels being treated as separate terms. The
*J* value and blank space indicating a missing level of a term are given
in the order of the corresponding calculated level if such a value is
available.

A question mark (?) following a level always indicates that the level may not
be real.

For levels having a configuration label, the question mark after the energy also implies that the correlation
of the calculated eigenvector to the experimental level is questionable. Sometimes,
instead of the question mark, we use the dagger symbol '†' after the level value. This notation is used mainly
for questionably assigned levels included in terms. An uncertain assignment of
an isolated level may be indicated by '†', but only if the configuration in the
first column would be unchanged by any possible reassignment of the level
(no question mark in the first column).

The values of certain levels in some spectra are followed by
"+*x*," and such notations may be extended to
"+*y*," "+*z*," etc., for additional sets of
levels of a particular spectrum. The relative positions of the levels within
such a system are accurate within experimental uncertainties, but no
experimental connection between this system and the other levels of the
spectrum has been made; the error of the assumed connection (estimated or
calculated) is represented by "+*x*."

The letter "*a*" following a level value indicates substantial
autoionization broadening. The decision whether to add this notation after a
particular level was more qualitative than quantitative, and no consistent
criteria were used for different spectra. Levels given with an
"*a*" for a particular spectrum may have autoionization rates
varying by several orders of magnitude. No indication of observed
autoionization broadening was given for many spectra. In no case should a level
lying above the principal ionization energy but given without an
"*a*" be assumed to have a small autoionization rate.

Some level energies are in square brackets "[ ]" and some are
in parentheses "( )". Square brackets indicate the energies
determined by interpolation, extrapolation, or other semi-empirical procedure
relying on some known experimental values. Parentheses indicate the energies
determined from *ab-initio* calculation or by other means not involving
evaluated experimental data. In ASD, they mostly occur for level data taken
from transition probability tables, for which experimental values could not
be found in NIST energy level compilations. Theoretical data may also be
given for hydrogen-like and helium-like spectra where the accuracy of
quantum-electrodynamic calculations often exceeds that of experimental
observations.

## [Go to top of page](#Top)  Uncertainty

Uncertainty of the level value is given a column next to level values, if it is available in ASD,
provided that the corresponding checkbox is checked in the input form. If no explicit information
about the uncertainty is available, it will be blank in the output. In such cases, the number of significant
figures in the level value gives an approximate estimate of the uncertainty. The ***uncertainty of
the level positions*** in units of the last decimal place is
not constant; it may vary by an order of magnitude even within a single analysis. If
no uncertainty value is available in ASD, it is usually safe to assume that the
probable error is between 2.5 and ~25 units in the last place. About 90 % of data in ASD
satisfies this assumption. A better estimate of the uncertainty in a particular case
may sometimes be obtained by consulting the original paper(s) or the line list.

The most accurate representation of the energy levels is in the default units of cm−1, as they are stored in ASD.
Conversion to other units (eV or Rydberg) involves an additional uncertainty of the conversion factor.
These factors, as well as their uncertainties, are taken from the latest [CODATA
recommended conversion factors](https://physics.nist.gov/cuu/Constants/energy.html). Before ASD version 5.5 of October 2017, uncertainties of these
conversion factors were not taken into account in the displayed data. Starting with v.5.5,
these uncertainties are combined in quadrature with the uncertainties of the stored data,
and the output quantities are rounded off according to the combined uncertainties. Thus, the
accuracy of the output energies is somewhat degraded when the units of eV or Rydberg are used.

All uncertainties given in ASD are meant to be on the level of one standard deviation.

## [Go to top of page](#Top)  Landé *g*: Experimental Magnetic Landé *g* Factor

These (dimensionless) magnetic splitting factors are usually obtained from
measurements of weak-field Zeeman patterns. The relation between the
uncertainty and the number of decimal places given differs according to the
observer and the particular value; the range covered by this relation is
similar to that for the level values (see above). More specific comments are
made on the *g* values for some spectra.

A colon following a *g* value indicates that it may be
significantly less accurate than values given to the same number of
decimal places but not so marked. Values followed by a question mark are
tentative, usually being based on assumptions made to allow reduction of
the Zeeman patterns.

## [Go to top of page](#Top)  Leading Percentages

This column normally gives one or two percentages from the calculated
eigenvector of the level. The space for the second percentage (on the right) is
used in either of two ways, as explained below. All percentages are rounded off
to the nearest percent, and the "%" symbol is omitted.

Any use of this column in a manner not outlined below is explained in
the tables for particular spectra as given in our compilations.

#### *First Percentages*

If the level has an assigned name, the first percentage is for this
"name" component. A first percentage followed by a term symbol
represents the largest component in the eigenvector of a level having no
assigned term name or named differently for bookkeeping purposes.
The configuration and ancestry for this component are shown
under "Configuration."

#### *Second Percentage from Same Eigenvector as First Percentage*

If two percentages are listed without the word "or " between them,
the second percentage is the largest of the remaining percentages from the same
eigenvector as the first percentage. If the second component belongs to the
same configuration as the first, we have in some cases omitted the
configuration after the second percentage and given only the parent terms (or
parent levels where appropriate) and final term for the second component. For
some spectra, a second component having both configuration and all parent terms
unchanged from the first component is given with only the final term. Electron
subshells common to different configurations for the first and second
percentages may be omitted from the second configuration. Term notations common
to all second percentages listed for the levels of a term may be given only
once.

The coupling scheme for a second eigenvector component belonging to a different
configuration may be different from the scheme for the first component; this
should not be confused with case (see below), where the second listed
percentage is the *leading* percentage in a different coupling scheme.

Since many authors list only the largest percentage for at least some levels,
the absence of a second percentage in this compilation does not necessarily
mean that it is less than the smallest percentage used here (0.5 %, given
as 1 %).

The relative signs of the two eigenvector components are not given. These are
often not given in the original publications. Furthermore, these signs depend
on certain conventions, no one set of which has been accepted by all authors.
The original articles can be consulted for (possibly) more complete
eigenvectors with signs.

#### *Second Percentage for Leading Component of Eigenvector in Alternate Coupling Scheme*

Where the eigenvectors from a calculation are available in more than one
coupling scheme, we often give in the second percentage space the leading
percentage from the eigenvector calculated in an alternate scheme. This use of
the second percentage space is indicated by the word "or" between the
two percentages, since each is a leading percentage. Competitively high
coupling purities for a configuration in different coupling schemes were, of
course, regarded as an argument for giving leading percentages in alternate
schemes, as was the case in which a second scheme for the configuration in
question is the preferred scheme for a related configuration (two
configurations connected by a strong transition array, etc.). We have favored
*LS* coupling as a second scheme in cases where another scheme was used
for naming the levels.

It should be noted that the leading component in a second scheme is not
necessarily a *name* for the level in that scheme; in cases of low
purity, the eigenvectors of two (or more) levels of the same *J*
value may have the same leading component.

For some configurations, the alternate coupling schemes are both *LS*
coupling, but with the electrons coupled differently in the two cases. In this
case it is usually possible to set up terms in either scheme (see
Eu I
4*f* 75*d*6*p*, for example).

## Bibliographic References

For information on viewing references, see the
[Locating references in the
ASD Bibliography](/PhysRefData/ASD/Html/help.html#VIEWREFS) section of the "Help" file.

## [Go to top of page](#Top)  Partition Function

If the electron temperature ***Te*** is entered in the entry page, a partition function ***Z***
defined as:  

*Z* = Σ*i(gi*·exp(-*Ei/Te*))

is printed at the bottom of the output page. Here ***i*** is the level number, ***gi*** is the
statistical weight of the atomic level, and ***Ei*** is the energy.

## [Go to top of page](#Top)  Creating an output for importing into a spreadsheet

Two options are available from the **Format Output** pull-down menu for creating an output in a format suitable for
importing into a spreadsheet: CSV (comma-separated ASCII file) or tab-delimited ASCII file. Both options produce output in the user's
browser window, which needs to be saved on the local computer by using the browser's interface options and opened with a spreadsheet software.
For importing data into Excel, the most convenient format is CSV. If the output is saved in a file with a .csv extension, some browsers
(e.g., Chrome) even allow the user to open it directly from the browser. Users of the OpenOffice software may prefer the tab-delimited format,
as it conveniently allows setting the format of all columns enclosed in double quotes as "text." This is required, for example, for
the *J*-values, which can be half-integers stored as strings, e.g., "1/2." If such columns are not set as text, the spreadsheet software
will most likely automatically convert them to dates. Even for columns containing only numbers, text format is needed to preserve the number of
decimal places, which indicates an implicit uncertainty of value. For this reason, the CSV-format output contains formulas instead of plain values.
After importing such a file into a spreadsheet, the user should "select all cells" (in Excel, this can be done by clicking on the small triangle
in the upper left corner of the spreadsheet), copy the selection, and paste it back as values.
[![Go to top of ASD Help](/Images/top.gif "Go to top of ASD Help")](/PhysRefData/ASD/Html/help.html)


---