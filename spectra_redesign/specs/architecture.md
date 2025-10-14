# Architecture Proposal and Framework Decision Matrix

The redesigned Spectra‑App must be a standalone Windows application with a modern, responsive interface and an extensible architecture.  After evaluating multiple technology stacks, we propose adopting **Qt for Python (PySide6)** as the primary UI framework, paired with a modular Python backend.  This document summarises the evaluation and outlines the high‑level architecture.

## Candidate Frameworks

Three desktop application stacks were considered:

1. **PySide6/Qt (Python)** – Official Python bindings for the Qt 6 framework.  Qt provides a comprehensive set of widgets, data‑driven views, charting facilities and a signal/slot mechanism for reactive programming.  According to a 2025 comparison of GUI frameworks, Qt (and thus PySide6) is “best for commercial, multimedia, scientific or engineering desktop applications” and allows developers to build modern interfaces that look native on Windows, macOS and Linux【337128316699931†L90-L112】.  Qt widgets use platform‑native components, ensuring that applications “look and feel at home” on each OS【337128316699931†L110-L112】.  Developers can install the library via `pip install pyside6`.  Packaging on Windows can be handled with PyInstaller or MSIX.

2. **Tauri (Rust core + web front‑end)** – A cross‑platform framework that couples a Rust backend with a secure WebView for the UI.  The official README states that Tauri builds “tiny, blazingly fast binaries for all major desktop platforms” and that developers can integrate any front‑end that compiles to HTML, CSS and JavaScript【807432203193955†L27-L31】.  Tauri uses the system webviews (e.g. WebView2 on Windows) and provides a built‑in bundler for formats such as `.exe` and `.msi`【807432203193955†L60-L64】.  The use of Rust for the core promises performance and safety, while the UI can leverage the rich ecosystem of web frameworks.

3. **.NET MAUI (C#)** – Microsoft’s cross‑platform framework for building native mobile and desktop apps with a single C# codebase.  The official site notes that .NET MAUI uses the latest technologies to build native apps on Windows, macOS, iOS and Android【527723963626351†L152-L156】 and allows developers to use a single codebase that “look and feel like the native platforms”【527723963626351†L160-L163】.  Visual Studio tooling provides hot reload, designer support and a growing set of open‑source controls【527723963626351†L167-L176】.  Packaging is handled by MSIX or EXE installers.

## Decision Matrix

| Criterion | PySide6/Qt | Tauri (Rust + Web) | .NET MAUI |
|---|---|---|---|
| **Language** | Python throughout; no context switching. | Rust backend, JS/TS front‑end; requires knowledge of multiple stacks. | C# (and XAML) for UI and logic. |
| **Cross‑platform support** | Windows, macOS, Linux and Android (via Qt6).  Packaging for Windows can produce an `.exe` or `.msix`. | Windows, macOS, Linux, iOS and Android; uses system webviews【807432203193955†L35-L38】. | Windows, macOS, iOS and Android【527723963626351†L152-L156】. |
| **UI look and feel** | Native widgets provide a professional appearance【337128316699931†L110-L112】; highly customisable via QStyles and Qt Designer. | Web front‑end can use modern design frameworks (e.g. React, Tailwind); consistent across platforms but may feel like a web app. | Native controls on each platform; modern look via Material Design and Fluent themes. |
| **Plotting and visualisation** | Qt Charts or integration with Matplotlib and Plotly via Qt WebEngine.  PySide6 can embed a `PlotWidget` for high‑performance charting. | Charting implemented in the web layer using libraries like Plotly.js or D3.js; performance depends on the browser engine. | Chart controls exist (e.g. Syncfusion, DevExpress) but may require commercial licences. |
| **Plugin/Extensibility** | Python is highly dynamic; plugins can be loaded via entry points or a `plugins/` folder. | Tauri provides a plugin system for Rust modules, but integrating Python plugins requires bridging via WebSockets or FFI. | .NET MAUI supports MEF or custom dependency injection; plugins compiled in C#. |
| **Performance** | Good for numerical operations via NumPy; UI responsiveness depends on Python’s GIL but can be mitigated with threads or QThreads. | Rust backend offers excellent performance and minimal binary size【807432203193955†L27-L31】; UI runs in a WebView. | Native performance due to AOT compilation; larger binary size and heavier tooling. |
| **Packaging & Distribution** | Use PyInstaller or Qt’s `windeployqt` to bundle dependencies into a single installer; typical size 60–100 MB. | Built‑in bundler produces small installers using system webviews【807432203193955†L60-L64】; must manage Rust toolchain and Node dependencies. | Uses MSIX packaging; requires Visual Studio and .NET SDK. |
| **Learning Curve** | Requires learning Qt’s signal/slot paradigm and widgets; Python developers can stay in one language. | Requires knowledge of Rust for the backend and modern web technologies for the UI; higher barrier of entry. | Requires C# and XAML; less familiar to pure Python developers. |
| **Licencing** | LGPL for Qt runtime; PySide6 is dual‑licensed under LGPL and commercial terms. | MIT or Apache 2.0 licence【807432203193955†L25-L31】; free and open source. | MIT licence for the framework; Visual Studio may require proprietary tools. |

## Recommendation

Given the project’s constraints and priorities—Python expertise, scientific computation, rapid development and need for a polished native UI—the recommended stack is **PySide6/Qt**.  Its native widgets provide the professional look required; it supports cross‑platform packaging while allowing the entire application to remain in Python.  The signal/slot architecture facilitates responsive interfaces without the double‑click issues seen in Streamlit.  While Tauri offers attractive packaging and a lightweight runtime, its Rust/JS split adds complexity and requires a web front‑end.  .NET MAUI delivers native experiences but would necessitate rewriting the data‑processing logic in C# and using Visual Studio.

## High‑Level Architecture

The redesigned application will be structured into distinct layers:

1. **Presentation Layer (UI)** – A PySide6 application using Qt Widgets.  The main window contains a menu bar and multiple tabs: **Data**, **Compare**, **Functional Groups**, **Similarity**, **History**, and **Settings**.  Each tab hosts its own widget stack.  The UI triggers commands to the service layer via signals.

2. **Service Layer** – Pure‑Python classes providing business logic: data ingestion, unit conversion, overlay management, differential operations, similarity computations and ML predictions.  These classes are independent of the UI and expose asynchronous methods where necessary.

3. **Data Layer** – Responsible for reading files, caching metadata and storing loaded spectra.  Implements a plugin interface for importers (e.g. CSV, JCAMP‑DX, FITS).  Maintains canonical internal units (wavelength in nm and flux in a chosen baseline) and returns views in other units.

4. **Plugin System** – A discovery mechanism (e.g. using Python entry points) that allows developers to add new importers, exporters, ML models or transform modules by dropping a package into a `plugins/` folder.  Each plugin includes a manifest describing its capabilities and dependencies.

5. **Provenance Service** – Generates and manages manifest files capturing the origin, units, transforms and citations for every derived dataset.  Exposes functions to create, read and validate manifests.  Integrates with the export wizard.

6. **Knowledge Log** – A module that writes structured messages to `docs/history/KNOWLEDGE_LOG.md` whenever the application ingests data, performs an operation or exports results.  Provides an API for the AI agent to read and append entries, ensuring continuity across sessions.

This modular architecture isolates the UI from core logic, enabling easier testing and future replacements of the presentation layer (e.g. a CLI or web interface).  Each layer communicates via well‑defined interfaces, promoting clarity and extensibility.