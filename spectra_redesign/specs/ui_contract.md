# User Interface Contract

This document specifies the expected behaviour and layout of the redesigned Spectra‑App desktop UI.  It serves as a contract between the design and implementation teams and provides guidance for developers and testers.

## 1. General Principles

- **Modern aesthetics:** The application must have a professional appearance, using native Qt widgets with custom styling inspired by contemporary scientific software.  Avoid 1990s‑era design cues【875267955107972†L19-L22】.
- **Single‑window design:** Users interact with a single main window containing multiple tabs; modal dialogs are used for settings and about information only when necessary.
- **Keyboard and accessibility:** All interactive elements must be reachable via keyboard navigation.  Provide accessible names and tooltips.  Support high‑contrast mode and a dark theme.
- **Responsive feedback:** Operations should provide immediate visual feedback via progress bars or toasts.  Errors must be reported clearly without dumping technical tracebacks to the user.

## 2. Main Window Layout

**Menu Bar** – Contains menus: **File**, **Edit**, **View**, **Tools**, **Help**.

- *File*: actions like **Open…**, **Import…**, **Export…**, **Save Session**, **Exit**.
- *Edit*: undo/redo, copy data, preferences.
- *View*: toggle dark mode, show/hide side panels, adjust legend positioning.
- *Tools*: access plugin manager, ML model manager, and data registry viewer.
- *Help*: open documentation, show about dialog, check for updates.

**Toolbar** – Quick actions: open file, add overlay, run difference/ratio, run functional‑group prediction, export snapshot.  Icons should have tooltips.

**Status Bar** – Displays concise messages (e.g. “Ready”, “Loading file…”) and the number of spectra loaded.  Long operations show a progress bar embedded in the status bar.

**Tab Widget** – Contains the following tabs:

1. **Data**
   - *Ingest Panel*: Drag‑and‑drop area and **Browse…** button.  Displays supported file types.  After ingestion, lists newly added spectra with basic metadata (label, points, units) and highlights duplicates.
   - *Units Panel*: Radio buttons or a dropdown to select the display unit for wavelength (nm, µm, Å, cm⁻¹) and for flux (transmittance, absorbance).  Changing the unit updates all visible plots via signals to the UnitsService.
   - *Spectrum List*: Table or list view showing all loaded spectra.  Columns: Name (editable), Source (file or provider), Points, Colour (with swatch), Visible (checkbox), Delete (button).  Dragging rows allows reordering.  Double‑clicking a name enters rename mode; single click is sufficient for selection (no double‑click requirement).

2. **Compare**
   - *Selection area*: Two dropdowns to select the spectra to operate on (A and B).  If only one spectrum is selected, operations requiring two are disabled.
   - *Operation buttons*: **Subtract (A − B)**, **Ratio (A / B)**, **Normalised Difference ((A − B)/(A + B))**, **Smoothing** (with slider to select window size).  Each operation triggers the MathService and displays results in the chart.
   - *Result plot*: The combined chart showing A, B and the result.  Users can toggle traces and adjust axis limits.  The legend collapses into a scrollable list if too many items are present.
   - *Result management*: Buttons to add the result to the overlay list, discard, or save as a separate dataset.

3. **Functional Groups**
   - *Prediction control*: Dropdown to select the ML model (default: built‑in IR functional group classifier) and a button to run predictions on the selected spectrum.
   - *Results panel*: Table listing predicted functional groups, wavenumber ranges and confidence scores.  The table supports sorting and filtering.
   - *Overlay options*: Checkboxes to overlay shaded bands on the current plot.  Bands use semi‑transparent colours distinct from spectra lines.  Users can adjust opacity.
   - *Citations*: A pane summarising the model’s provenance and training data.

4. **Similarity**
   - *Database selection*: Dropdown listing available datasets (e.g. local sample library, NIST library, user‑added databases).  Provide a **Manage…** button to add or remove datasets.
   - *Query selection*: Dropdown to select a query spectrum from those loaded.
   - *Parameters*: Choice of distance metric (cosine, Euclidean, correlation) and number of results to return.
   - *Run search* button: Executes similarity search via SimilarityService.  Results appear in a table with columns: Name, Score, Dataset, Actions (overlay button).

5. **History**
   - *Log viewer*: Scrollable list showing entries from `KNOWLEDGE_LOG.md`.  Each entry displays timestamp, type (import, operation, prediction, export), summary and link to more details.
   - *Filters*: Date range picker, type filter, text search.
   - *Details pane*: Clicking an entry opens a modal showing the full metadata and provenance from the manifest.

6. **Settings** (modal dialog)
   - *General*: default wavelength and flux units, startup behaviour (restore last session), dark/light mode.
   - *Plugins*: list of discovered plugins with options to enable/disable and view details.  Button to scan for new plugins.
   - *Provenance*: fields to set default citation information (e.g. user name, institution) that will be recorded in manifests.

## 3. Interaction and Behaviour Rules

1. **No double‑clicks required:** All actions are triggered by single clicks or keyboard shortcuts.  Double‑clicks are reserved for editing fields (e.g. renaming a spectrum).
2. **Undo/redo:** Most operations (add, remove, rename, differential, prediction) support undo and redo via Ctrl‑Z / Ctrl‑Y.  Actions are recorded in a command stack.
3. **Asynchronous operations:** File ingestion, network fetches, ML predictions and similarity searches run in background threads.  The UI displays a spinner or progress bar and disables relevant controls until completion.
4. **Error reporting:** Errors are displayed as non‑blocking toast notifications with an optional “Details…” link that opens a modal with the traceback.  Errors are also logged to file and recorded in the knowledge log.
5. **Contextual help:** Each panel contains a help icon or hint text linking to the documentation.  Tooltips provide concise explanations of controls and units.

## 4. Layout Guidelines

* Use a consistent spacing (8 px) between widgets.
* Align labels and input fields in forms.
* Do not overcrowd side panels; prefer collapsible sections when many options are present.
* Charts should resize with the window and maintain aspect ratio.  Axes should automatically adjust ranges but allow manual override.
* Colours: Choose a distinct palette for up to 10 overlays; beyond this, assign random but perceptually distinct colours.  Provide a colour picker per trace in the Spectrum List.

## 5. Accessibility

* Provide high‑contrast and dark modes toggled in the Settings dialog.
* Support screen readers by setting accessible names on widgets.
* Ensure tab order follows the visual layout.
* Use font sizes and spacing consistent with accessibility guidelines.

## 6. Internationalisation

Design the UI with translation in mind: all strings should be stored in translation files (e.g. Qt’s `*.ts` files) and loaded at runtime.  The initial version will be in English, with provisions for future localisations.

## 7. Summary

This UI contract defines the structure, interaction patterns and styling for the Spectra‑App desktop application.  It seeks to provide a modern, intuitive and accessible experience while exposing the app’s rich functionality through a clear navigation hierarchy.  Developers must adhere to this contract when implementing the PySide6 front‑end, and testers should use it as a checklist for verifying UI behaviour.