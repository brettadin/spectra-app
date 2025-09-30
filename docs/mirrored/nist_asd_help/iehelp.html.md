[![[skip navigation]](/Images/dot_t.gif "skip navigation")](#start)






[![Go to top of ASD Help](/Images/top.gif "Go to top of ASD Help")](/PhysRefData/ASD/Html/help.html) 
The ASD database provides data on ground states and ionization energies for atoms and atomic ions. For more
information consult [Introduction to and Contents of the ASD](/PhysRefData/ASD/Html/contents.html).

---



## Ground States and Ionization Energies (GSIE) Search Form

This search form, referred to as the GSIE Form, provides access to
the ground state specifications, ionization energies, and total binding energies data.
Submitting information provided by the user on the GSIE Form
generates a list of GSIE data for specified spectra (elements and ionization stages).

At a minimum, the user must enter the [spectra](#IE_SPECTRA) of interest
(e.g., C I) and then click "Retrieve Data".

The GSIE Search Form prompts the user for the following information:

* [Spectra](#IE_SPECTRA) of interest (e.g., Fe or H-DS I).
* Ionization or binding energy units (selected from the pulldown menu).
    
   The energies may be displayed in one of the following units:
  + cm−1 (reciprocal centimeter or wavenumber)
  + eV (electron Volt), the default unit
  + Rydberg
  + Hartree (=2×Rydberg)
  + GHz
* Choice of viewing the output as an HTML table or an ASCII table (selected from the pulldown menu).
* Choice of energy ordering of the output, i.e., ordered by the nuclear charge *Z* (default)
  or by isoelectronic sequences.
* Choice of the output information.  
    
  In particular, the user can choose to display the total binding energies instead of
  the ionization energies, which are selected by default.
* Choice of the output of the relevant available bibliographic references.  
  For all GSIE data, bibliographic references are available and can be
  retrieved by selecting the "Bibliographic references" checkbox.

For GSIE output, the default is to display the following data:

* Atomic number
* Spectrum name
* Ion charge
* Isoelectronic sequence symbol
* Ionization energy
* Uncertainty
* Ground-state electronic shells
* Ground-state level label
* Ionized configuration (i.e., configuration and level labels and the *J*
  value of the level of the next ion, to which the given ionization energy corresponds).
* Bibliographic References

To suppress display of any of the information listed above, the corresponding
checkbox can be unclicked.

---



## [Go to top of page](#Top)   Selecting Spectra for GSIE Searches

The Ground States and Ionization Energies (GSIE) Spectra input box works in exactly
the same way as the [Spectra input box in the Line Search](/PhysRefData/ASD/Html/lineshelp.html#LINES_SPECTRA).
  
  

#### *Examples of most common Spectra for the GSIE Search*

|  |  |
| --- | --- |
| **To specify** | **Enter** |
| All neutral atoms | H-Ds I |
| All spectra of sodium | Na |
| Spectra of all elements between Ne and Fe in   isoelectronic sequences between Ne-like and S-like | Ne-Fe Ne-like-S-like |
| Lithium-like magnesium | Mg x |
| Lithium-like magnesium | mg Li-like |
| Singly-ionized 11B | 11B II |

---



## [Go to top of page](#Top)   Output for GSIE (by table column heading)

* **Atomic Number**: Number of protons in the atomic nucleus.
* **Spectrum Name**: Standard spectroscopic notation, i.e., the
  element symbol followed by the Roman number of the spectrum (equal to the ion charge plus one).
* **Ion Charge:** Electric charge of the atom or ion.
* **Element name:** Standard name of the chemical element, according to
   [NIST Periodic Table of the Elements](https://www.nist.gov/pml/periodic-table-elements)
* **Isoelectronic sequence:** Chemical symbol of the neutral atom having the same
  number of electrons as the given ion.
* [**Ground Shells**](#IEGROUNDSHELLS)
* [**Ground Configuration**](#IEGROUNDCONF)
* [**Ground Level**](#IEGROUNDLEV)
* [**Ionized Level**](#IEIONIZEDLEV)
* [**Ionization Energy:**](#IEIE) The minimum energy required to remove one electron from the
  atom or ion in its ground state.
* [**Total Binding Energy:**](#IEBE) The minimum energy required to remove all electrons from the
  atom or ion in its ground state. It is calculated online by summing up all relevant ionization energies.
* [**Uncertainty**](#IEUNC)
* [**Bibliographic References**](#IEBIBREF)

---

The ground shells designation is given in groups of symbols: an integer number corresponding to the
principal quantum number of the shell, followed by the standard electronic shell symbol (e.g., *s*,
*p*, *d*) with a superscript indicating the number of electrons the shell ("1" is omitted for brevity).

For complex atoms and ions with a large number of occupied electronic shells, certain groups of fully-occupied shells
are designated with an element symbol corresponding to a neutral atom having these fully occupied shells in its ground state,
given in square brackets before the list of outer shells. These shell groups are listed below:

* [Ne] = 1s22s22p6,
* [Ar] = 1s22s22p63s23p6,
* [Kr] = 1s22s22p63s23p63d104s24p6,
* [Cd] = 1s22s22p63s23p63d104s24p64d105s2,
* [Xe] = 1s22s22p63s23p63d104s24p64d105s25p6,
* [Hg] = 1s22s22p63s23p63d104s24p64d105s25p64f145d106s2,
* [Rn] = 1s22s22p63s23p63d104s24p64d105s25p64f145d106s26p6

In this column, ASD gives the electronic configuration for the largest component in the calculated
eigenvector of the ground level. These largest components are determined by theoretical calculations involving various approximations.
Thus, some uncertainties are involved, especially for complex heavy atoms or ions.
Any ancestor [terms](/PhysRefData/ASD/Html/levelshelp.html#LOUTTERM) or
[*J*](/PhysRefData/ASD/Html/levelshelp.html#LOUTJ) values appropriate to this
eigenvector component are normally included with the configuration, as in the examples in the
[Introduction to Atomic Spectroscopy](https://www.nist.gov/pml/atomic-spectroscopy-different-coupling-schemes).

See more about configuration designations in the [Help for Levels](/PhysRefData/ASD/Html/levelshelp.html#LOUTCONFIG) sections
and in the [Introduction to Atomic Spectroscopy](https://www.nist.gov/pml/atomic-spectroscopy-different-coupling-schemes).

In this column, ASD gives the [term](/PhysRefData/ASD/Html/levelshelp.html#LOUTTERM) symbol
and [*J*](/PhysRefData/ASD/Html/levelshelp.html#LOUTJ) value for the largest component in the calculated
eigenvector of the ground level. As with the configurations (see above), some uncertainties may be involved, especially for complex heavy atoms or ions.
Designations given in this column include the [configuration, term, and *J* value](#IEGROUNDCONF) corresponding to the ground
state of the next ion (i.e., the ion obtained by removing one electron from the given atom or ion).
This quantity is the minimum energy required to remove one electron from the
atom or ion in its ground state. The ionization energies are stored in the
database in units of cm−1. Output in these units gives the most
accurate values. Conversion to other units (eV or Rydberg) involves an
additional uncertainty of the conversion factor. These factors, as well as
their uncertainties, are taken from the latest
[CODATA
recommended conversion factors](https://physics.nist.gov/cuu/Constants/energy.html). Before ASD version 5.5 of October 2017,
uncertainties of these conversion factors were not taken into account in the
displayed data. Starting with v.5.5, these uncertainties are combined in
quadrature with the uncertainties of the stored data, and the output
quantities are rounded off according to the combined uncertainties. Thus, the
accuracy of the output energies is somewhat degraded when the units of eV or
Rydberg are used.

Some ionization energies are in square brackets "[ ]" and some
are in parentheses "( )". Square brackets indicate the
energies determined by interpolation, extrapolation, or other semi-empirical
procedure relying on some known experimental values. Parentheses indicate
energies that have been determined from an *ab-initio* calculation, or are
otherwise not derived from evaluated experimental data. Theoretical values
are typically given for highly-ionized spectra, where experimental data are
scarce. Theoretical data may also be given for hydrogen-like and
helium-like spectra, where the accuracy of quantum-electrodynamic calculations
often exceeds that of experimental observations.

This quantity is the minimum energy required to remove all electrons from the
atom or ion in its ground state. It is calculated online by summing up all
relevant ionization energies. If the calculation involves some experimental or
semi-empirical ionization energies, the value of the binding energy is
treated as semiempirical and is enclosed in square brackets. If all the
involved ionization energies are purely theoretical, the resulting binding
energy is also considered to be theoretical and appears in the output enclosed
in parentheses.
Uncertainty of the ionization or binding energy value is given in a column
next to the energy value, if it is available in ASD, provided that the
corresponding checkbox is checked in the input form. If no explicit
information about the uncertainty is available, it will be blank in the output.
In such cases, the number of significant figures in the energy value gives an
approximate estimate of the uncertainty. It is usually safe to assume that the
probable error is between 2.5 and ~25 units in the last place. About
90 % of data in ASD satisfies this assumption. A better estimate of the
uncertainty in a particular case may sometimes be obtained by consulting the
original paper(s).

Note that, if the output is requested in the default units of eV or in the
Rydberg units, the displayed uncertainties include the uncertainties of the
corresponding conversion factors from the units of cm−1. See more
about this in the section for [Ionization Energy](#IEIE).

For binding energies (determined as a sum of ionization energies of
consecutive ionization stages), uncertainties are estimated from those of the
ionization energies involved. Uncertainties of ionization energies taken from
the same literature source are summed up linearly, assuming they are dominated
by systematics. Uncertainties resulting from different sources are summed up
in quadrature. If the uncertainty of an ionization energy involved in the
summation is unknown, it is estimated as ten units of the least significant
figure of the ionization energy.

## [Go to top of ASD Help](/PhysRefData/ASD/Html/help.html)  Bibliographic References

For information on viewing the references, see the
[Locating references in the
ASD Bibliography](/PhysRefData/ASD/Html/help.html#VIEWREFS) section of the "Help" file.

---