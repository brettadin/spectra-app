# Mast.Catalogs.Filtered.Tic

Get TESS Input Catalog entries by filtering based on column (as in Advanced Search). Note: It is recommended to use Mast.Catalogs.Filtered.Tic.Rows to download results.

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

[Example (Python)](pyex.html#MastCatalogsFilteredTicPy)

# Mast.Catalogs.Filtered.Tic.Rows

Get TESS Input Catalog entries by filtering based on column (as in Advanced Search). Note: This can only return rows of data, not counts, but is faster than passing c.\* as the filters to Mast.Catalogs.Filtered.Tic.

### Parameters

* **columns:** string (required) Specifies the columns to be returned as a comma-separated list, e.g. "ID, ra, dec". "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

[Example (Python)](pyex.html#MastCatalogsFilteredTicRowsPy)

# Mast.Catalogs.Filtered.Tic.Position

Get TESS Input Catalog entries by performing a cone search as well as filtering based on column (as in Advanced Search). Note: It is recommended to use Mast.Catalogs.Filtered.Tic.Position.Rows to download results.

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.   
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".
* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsFilteredTicPositionPy)

# Mast.Catalogs.Filtered.Tic.Position.Rows

Get TESS Input Catalog entries by performing a cone search as well as filtering based on column (as in Advanced Search). Note: This can only return rows of data, not counts, but is faster than passing c.\* as the filters to Mast.Catalogs.Filtered.Tic.Position.

### Parameters

* **columns:** string (required) Specifies the columns to be returned as a comma-separated list, e.g. "ID, ra, dec". "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.   
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".
* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsFilteredTicPositionRowsPy)

# Mast.Catalogs.Tic.Cone

Perform a TESS Input Catalog cone search. See [TIC Field documentation](_t_i_cfields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (default 0.02) Search radius in decimal degrees.

### Notes

[MashupRequest](class_mashup_1_1_mashup_request.html) property pagesize rows up to nr will be returned. The [MashupRequest](class_mashup_1_1_mashup_request.html) property page should be used to get subsequent pages.

[Example (Python)](pyex.html#MastCatalogsTicConePy)

# Mast.Tic.Crossmatch

Perform a cross-match with the TESS Input Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastTicCrossmatchPy)

# Mast.Catalogs.Filtered.Ctl

Get TESS Candidate Target List entries by filtering based on column (as in Advanced Search). Note: It is recommended to use Mast.Catalogs.Filtered.Ctl.Rows to download results.

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

[Example (Python)](pyex.html#MastCatalogsFilteredCtlPy)

# Mast.Catalogs.Filtered.Ctl.Rows

Get TESS Candidate Target List entries by filtering based on column (as in Advanced Search). Note: This can only return rows of data, not counts, but is faster than passing c.\* as the filters to Mast.Catalogs.Filtered.Ctl.

### Parameters

* **columns:** string (required) Specifies the columns to be returned as a comma-separated list, e.g. "ID, ra, dec". "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

[Example (Python)](pyex.html#MastCatalogsFilteredCtlRowsPy)

# Mast.Catalogs.Filtered.Ctl.Position

Get TESS Candidate Target List entries by performing a cone search as well as filtering based on column (as in Advanced Search). Note: It is recommended to use Mast.Catalogs.Filtered.Ctl.Position.Rows to download results.

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.   
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".
* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsFilteredCtlPositionPy)

# Mast.Catalogs.Filtered.Ctl.Position.Rows

Get TESS Candidate Target List entries by performing a cone search as well as filtering based on column (as in Advanced Search). Note: This can only return rows of data, not counts, but is faster than passing c.\* as the filters to Mast.Catalogs.Filtered.Ctl.Position.

### Parameters

* **columns:** string (required) Specifies the columns to be returned as a comma-separated list, e.g. "ID, ra, dec". "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.   
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [TIC Field documentation](_t_i_cfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".
* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsFilteredCtlPositionRowsPy)

# Mast.Catalogs.Ctl.Cone

Perform a TESS Candidate Target List cone search. See [TIC Field documentation](_t_i_cfields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (default 0.02) Search radius in decimal degrees.

### Notes

[MashupRequest](class_mashup_1_1_mashup_request.html) property pagesize rows up to nr will be returned. The [MashupRequest](class_mashup_1_1_mashup_request.html) property page should be used to get subsequent pages.

[Example (Python)](pyex.html#MastCatalogsCtlConePy)

# Mast.Ctl.Crossmatch

Perform a cross-match with the TESS Candidate Target List.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastCtlCrossmatchPy)

# Mast.Catalogs.Filtered.Wfc3Psf.Uvis

Get WFC3 PSF UVIS by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "F8%".

[Example (Python)](pyex.html#MastCatalogsFilteredWfc3PsfUvisPy)

# Mast.Catalogs.Filtered.Wfc3Psf.Ir

Get WFC3 PSF IR by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "F8%".

[Example (Python)](pyex.html#MastCatalogsFilteredWfc3PsfIrPy)

# Vo.Hesarc.DatascopeListable

Perform a VO cone search.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (default 0.02) Search radius in decimal degrees.

### Notes

With all return types other than csv the result will include the fields "status" and "percent complete." While the query is still running the status will be "EXECUTING" and the percent complete will reflect what percentage of the results have been returned. Once the query is finished, the status will change to "COMPLETE" and percent complete will be 1.   
There is a inactivity time out of 10 minutes, which is the maximum time between requests for a query not to be aborted.

[Example (Python)](pyex.html#VoHesarcDatascopeListablePy)

# Mast.Caom.Cone

Perform a CAOM cone search. See [CAOM Field documentation](_c_a_o_mfields.html) for the list of columns returned.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (default 0.2) Search radius in decimal degrees.
* **exclude\_hla:** boolean (default false) If true excludes HLA results

[Example (Python)](pyex.html#MastCaomConePy)

# Mast.Caom.Filtered

Get MAST observations by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [CAOM Field documentation](_c_a_o_mfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

[Example (Python)](pyex.html#MastCaomFilteredPy)

# Mast.Caom.Filtered.Position

Get MAST observations by performing a cone search as well as filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.   
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [CAOM Field documentation](_c_a_o_mfields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".
* **position:** string (required) Gived the position and radius for the cone search part of the query in the form "ra, dec, radius."

[Example (Python)](pyex.html#MastCaomFilteredPositionPy)

# Mast.Caom.Products

Get data products for a specific observation. See [Products Field documentation](_productsfields.html) for the list of columns returned.

### Parameters

* **obsid:** int or str (default 1000033356) One or more product group IDs for which data products will be returned. If supplying more than one obsid the fromat is a comma separated string.

  Note:\*\* When doing a product query for HST data, there will be no indication if that data is in the queue for reprocessing. If this information is crucial, currently, one must go through the MAST Portal.

[Example (Python)](pyex.html#MastCaomProductsPy)

# Mast.Caom.Crossmatch

Perform a cross-match with all MAST data.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec colums (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastCaomCrossmatchPy)

# Mast.Hsc.Db.v2

Perform a Hubble Source Catalog v2 cone search. See [HSC Field documentation](_h_s_cfields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (default 0.02) Search radius in decimal degrees.
* **nr:** int (default 50000) Maximum number of records to return.
* **ni:** int (default 1) Minimum number of color images with detected sources in a match.
* **magtype:** int (default 1) A magtype of 1 corresponds to MagAper2, 2 is MagAuto.

### Notes

[MashupRequest](class_mashup_1_1_mashup_request.html) property pagesize rows up to nr will be returned. The [MashupRequest](class_mashup_1_1_mashup_request.html) property page should be used to get subsequent pages.

[Example (Python)](pyex.html#MastHscDbv2Py)

# Mast.Hsc.Db.v3

Perform a Hubble Source Catalog v3 cone search. See [HSC Field documentation](_h_s_cfields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (default 0.02) Search radius in decimal degrees.
* **nr:** int (default 50000) Maximum number of records to return.
* **ni:** int (default 1) Minimum number of color images with detected sources in a match.
* **magtype:** int (default 1) A magtype of 1 corresponds to MagAper2, 2 is MagAuto.

### Notes

[MashupRequest](class_mashup_1_1_mashup_request.html) property pagesize rows up to nr will be returned. The [MashupRequest](class_mashup_1_1_mashup_request.html) property page should be used to get subsequent pages.

[Example (Python)](pyex.html#MastHscDbv3Py)

# Mast.HscMatches.Db.v2

Get detailed results for an HSCv2 match. See [HSC\_Matches Field documentation](_h_s_c__matchesfields.html) for a description of the returned columns.

### Parameters

* **input:** int (default 11599418) The âMatch IDâ of an HSC object.

[Example (Python)](pyex.html#MastHscMatchesDbv2Py)

# Mast.HscMatches.Db.v3

Get detailed results for an HSCv3 match. See [HSC\_Matches Field documentation](_h_s_c__matchesfields.html) for a description of the returned columns.

### Parameters

* **input:** int (default 11599418) The âMatch IDâ of an HSC object.

[Example (Python)](pyex.html#MastHscMatchesDbv3Py)

# Mast.HscSpectra.Db.All

Get all the HSC spectra. See [HSC\_Spectra Field documentation](_h_s_c__spectrafields.html) for a description of the returns columns.

### Parameters

None, the request simply returns all the HSC spectra

[Example (Python)](pyex.html#MastHscSpectraDbAllPy)

# Mast.Hsc.Crossmatch.MagAper2v3

Perform a cross-match with the Hubble Source Catalog V3.0, MagAper2.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastHscCrossmatchMagAper2v3Py)

# Mast.Hsc.Crossmatch.MagAutov3

Perform a cross-match with the Hubble Source Catalog V3.0, MagAuto.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastHscCrossmatchMagAutov3Py)

# Mast.Catalogs.DiskDetective.Cone

Perform a Disk Detective cone search. See [Disk\_Detective Field documentation](_disk__detectivefields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (default 0.02) Search radius in decimal degrees.

### Notes

[MashupRequest](class_mashup_1_1_mashup_request.html) property pagesize rows up to nr will be returned. The [MashupRequest](class_mashup_1_1_mashup_request.html) property page should be used to get subsequent pages.

[Example (Python)](pyex.html#MastCatalogsDiskDetectiveConePy)

# Mast.Catalogs.Filtered.DiskDetective.Count

Get number of Disk Detective results based on column(s) (as in Advanced Search).

### Parameters

* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [Disk\_Detective Field documentation](_disk__detectivefields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

[Example (Python)](pyex.html#MastCatalogsFilteredDiskDetectiveCountPy)

# Mast.Catalogs.Filtered.DiskDetective.Position.Count

Get number of Disk Detective results by performing a cone search as well as filtering based on column (as in Advanced Search).

### Parameters

* **filters:** list of json objects (required) List of the filters to be applied.   
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [Disk\_Detective Field documentation](_disk__detectivefields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".
* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsFilteredDiskDetectivePositionCountPy)

# Mast.Catalogs.Filtered.DiskDetective

Get Disk Detective results by filtering based on column (as in Advanced Search).

### Parameters

* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [Disk\_Detective Field documentation](_disk__detectivefields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

[Example (Python)](pyex.html#MastCatalogsFilteredDiskDetectivePy)

# Mast.Catalogs.Filtered.DiskDetective.Position

Get Disk Detective results by performing a cone search as well as filtering based on column (as in Advanced Search).

### Parameters

* **filters:** list of json objects (required) List of the filters to be applied.   
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [Disk\_Detective Field documentation](_disk__detectivefields.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".
* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsFilteredDiskDetectivePositionPy)

# Mast.GaiaDR1.Crossmatch

Perform a cross-match with the Gaia (DR1) Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastGaiaDR1CrossmatchPy)

# Mast.GaiaDR2.Crossmatch

Perform a cross-match with the Gaia (DR2) Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastGaiaDR2CrossmatchPy)

# Mast.GaiaDR3.Crossmatch

Perform a cross-match with the Gaia (DR3) Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

Example (Python)

# Mast.Tgas.Crossmatch

Perform a cross-match with the TGAS (DR1) Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastTgasCrossmatchPy)

# Mast.Catalogs.GaiaDR1.Cone

Perform GAIA (DR1) catalog cone search. See [Gaia Field documentation](_gaiafields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsGaiaDR1ConePy)

# Mast.Catalogs.GaiaDR2.Cone

Perform GAIA (DR2) catalog cone search. See [Gaia Field documentation](_gaiafields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsGaiaDR2ConePy)

# Mast.Catalogs.GaiaDR3.Cone

Perform GAIA (DR3) catalog cone search. See [Gaia Field documentation](_gaiafields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

Example (Python)

# Mast.Catalogs.Tgas.Cone

Perform TGAS (DR1) catalog cone search. See [Gaia Field documentation](_gaiafields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.

[Example (Python)](pyex.html#MastCatalogsTgasConePy)

# Mast.Name.Lookup

Resolves an object name into a position on the sky.

### Parameters

* **input:** string (required) The object name to be resolved.
* **format:** string (default xml) The return type, options are xml and json.

[Example (Python)](pyex.html#MastNameLookupPy)

# Mast.Missions.List

Lists the missions available in CAOM.

### Parameters

None, the request simple returns all CAOM missions.

[Example (Python)](pyex.html#MastMissionsListPy)

# Mast.Galex.Crossmatch

Perform a cross-match with the GALEX Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastGalexCrossmatchPy)

# Mast.Sdss.Crossmatch

Perform a cross-match with the Sloan Digital Sky Surveys (SDSS) Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#MastSdssCrossmatchPy)

# Mast.2Mass.Crossmatch

Perform a cross-match with the Two Micron All Sky Survey (2MASS) Catalog.

### Parameters

* **raColumn:** string (default 'ra') The name of the ra column in the uploaded data from which to perform the cross-match.
* **decColumn:** string (default 'dec') The name of the dec column in the uploaded data from which to perform the cross-match.
* **radius:** float (default 0.002) The radius over which to perform the cross-match.

### Notes

When using this service, a json object must be provided in the [MashupRequest](class_mashup_1_1_mashup_request.html) property "data" that at minimum contains ra and dec columns (see the python example for a minimal example of this object). If using the json result from a CAOM cone search as crossmatch input the ra/dec columns will usually be 's\_ra' and s\_dec.'

[Example (Python)](pyex.html#Mast2MassCrossmatchPy)

# Vo.Generic.Table

Get VO data given a url.

### Parameters

* **url:** str (required) The url to query.

[Example (Python)](pyex.html#VoGenericTablePy)

# Mast.Galex.Catalog

Perform a GALEX catalog cone search. See [GALEX Field documentation](_g_a_l_e_xfields.html) for a description of the returned columns.

### Parameters

* **ra:** float (required) Right ascension in decimal degrees.
* **dec:** float (required) Declination in decimal degrees.
* **radius:** float (required) Search radius in decimal degrees.
* **maxrecords:** in (default 10000) Maximum number of records to return.

[Example (Python)](pyex.html#MastGalexCatalogPy)

# Mast.Jwst.Filtered.Nircam

Get JWST Science Instrument Keyword entries for NIRCAM by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [JWST Instrument Field documentation](_jwst_inst_keywd.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

# Mast.Jwst.Filtered.Niriss

Get JWST Science Instrument Keyword entries for NIRISS by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [JWST Instrument Field documentation](_jwst_inst_keywd.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

# Mast.Jwst.Filtered.Nirspec

Get JWST Science Instrument Keyword entries for NIRSPEC by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [JWST Instrument Field documentation](_jwst_inst_keywd.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

# Mast.Jwst.Filtered.Miri

Get JWST Science Instrument Keyword entries for MIRI by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [JWST Instrument Field documentation](_jwst_inst_keywd.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

# Mast.Jwst.Filtered.Fgs

Get JWST Science Instrument Keyword entries for FGS by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [JWST Instrument Field documentation](_jwst_inst_keywd.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

# Mast.Jwst.Filtered.GuideStar

Get JWST Science Instrument Keyword entries for GuideStar by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [JWST Instrument Field documentation](_jwst_inst_keywd.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".

# Mast.Jwst.Filtered.Wss

Get JWST Science Instrument Keyword entries for WSS by filtering based on column (as in Advanced Search).

### Parameters

* **columns:** string (required) Specifies the columns to be returned. "COUNT\_BIG(\*)" will return the number of observations returned from the query, but does not return the results themselves. "c.\*" will return all the columns, as in a CAOM cone search.
* **filters:** list of json objects (required) List of the filters to be applied.  
  A Filter has the form:  
  + **paramName:** Required string giving the column being filtered.
  + **values:** Required list of acceptable values for the column. If the column has discrete values the list will be of the form [val1,val2], and the values will be matched exactly. If the column is continuous the list will be of the form [{"min":minval,"max":maxval}]. If using the freeText parameter, values may be an empty list ([]).
  + **separator:** Optional string giving the separator for a multi-valued column (see [JWST Instrument Field documentation](_jwst_inst_keywd.html) for which columns are multi-valued).
  + **freeText:** Optional string, free text to search for in the column. Allows wildcarding, but must be explicit. Wildcard character is "%". E.g. "ex%planet%".