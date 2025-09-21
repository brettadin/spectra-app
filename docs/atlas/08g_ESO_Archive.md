# 📄 08g_ESO_Archive.md

## Atlas Foundation — Section 08g  
**Target:** ESO Archive (European Southern Observatory)

---

### 🌍 Overview
The **ESO Science Archive Facility** is the primary repository for data obtained with ESO’s telescopes and instruments (e.g., VLT, La Silla, ALMA collaboration data).  
It provides raw, calibrated, and science-ready data with associated metadata and calibration files.

- URL: [https://archive.eso.org/](https://archive.eso.org/)  
- API Docs: [https://archive.eso.org/cms/eso-data/science-archive-services.html](https://archive.eso.org/cms/eso-data/science-archive-services.html)

---

### 📊 Data Coverage
- **Optical/NIR data** from **VLT, VISTA, VST, La Silla**.  
- **Radio/Sub-mm** via **ALMA (European ARC node)**.  
- **Calibration & pipeline products**: Reduced images, spectra, cubes.  
- Cross-linked to proposals, publications, and instrument documentation.

---

### 🔌 Access Methods
1. **Web GUI**:  
   - Search by object name, coordinates, program ID, instrument, PI.  
   - Supports batch query and download.

2. **HTTP/FTP direct download**:  
   - Once dataset IDs are known, bulk retrieval possible.

3. **VO (Virtual Observatory) Services**:  
   - **TAP (Table Access Protocol)** for catalog queries.  
   - **SIAP (Simple Image Access Protocol)** for images.  
   - **SSAP (Simple Spectral Access Protocol)** for spectra.  

4. **Programmatic Access (Python)**:  
   - Via **astroquery.eso** module.  
   - Handles login (for proprietary data), query, and download.

---

### 🐍 Example (Astroquery)
```python
from astroquery.eso import Eso

eso = Eso()
eso.login("your_username")  # Only for proprietary data

# Example: search observations of NGC 1068 with X-Shooter
result = eso.query_instrument("xshooter", target="NGC 1068")
print(result)

# Download the first dataset
if len(result) > 0:
    files = eso.retrieve_data(result['DP.ID'][0])
    print("Downloaded:", files)
```

---

### ⚠️ Quirks & Challenges
- **Login required** for proprietary or still-protected data.  
- **Rate limiting** may occur on large bulk downloads.  
- **Calibration association** can be complex: some instruments require fetching multiple files for a complete reduction.  
- **Astroquery.eso** sometimes lags behind ESO’s evolving API (workarounds may be required).  

---

### 🧭 How to Use in Our Atlas
- ESO fills the **ground-based optical/NIR + sub-mm niche**, complementing space missions (MAST, HST, JWST, GAIA).  
- Provides **spectral diversity** (long-baseline interferometry, adaptive optics, radio-sub-mm).  
- Integration point for **cross-matching targets**: objects observed both by ESO instruments and space telescopes.  
- Will require a **fetcher module** (e.g., `app/server/fetchers/eso_fetcher.py`) with:
  - TAP query for metadata
  - Astroquery interface for spectra/images
  - Provenance logging for instrument, program ID, PI, and calibration status.

---

### 📌 Next Steps
- Define ESO fetcher stub in `fetch_archives.py`.  
- Expand Atlas with **instrument mapping** (X-Shooter, UVES, MUSE, etc.).  
- Test astroquery workflows with a few bright targets (e.g., NGC 1068, Betelgeuse).  

---

✅ This is **08g — ESO Archive** for your Atlas.
