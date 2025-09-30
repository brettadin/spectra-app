### 1. Public access

#### 1.1. Query object

This query searches for all the objects contained in an arbitrary rectangular projection of the sky.

WARNING: This method implements the ADQL BOX function that is deprecated in the latest version of the standard
(ADQL 2.1, see: <https://ivoa.net/documents/ADQL/20231107/PR-ADQL-2.1-20231107.html#tth_sEc4.2.9>).

It is possible to choose which data release to query, by default the Gaia DR3 catalogue is used. For example

```
>>> from astroquery.gaia import Gaia
>>> Gaia.MAIN_GAIA_TABLE = "gaiadr2.gaia_source"  # Select Data Release 2
>>> Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"  # Reselect Data Release 3, default
```

The following example searches for all the sources contained in an squared region of side = 0.1
degrees around an specific point in RA/Dec coordinates. The results are sorted by distance (`dist`) in ascending order.

```
>>> import astropy.units as u
>>> from astropy.coordinates import SkyCoord
>>> from astroquery.gaia import Gaia
>>>
>>> coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
>>> width = u.Quantity(0.1, u.deg)
>>> height = u.Quantity(0.1, u.deg)
>>> r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
INFO: Query finished. [astroquery.utils.tap.core]
>>> r.pprint(max_lines=12, max_width=130)
         dist             solution_id             designation          ... ebpminrp_gspphot_upper libname_gspphot
                                                                 ...                mag
--------------------- ------------------- ---------------------------- ... ---------------------- ---------------
0.0026043272506261527 1636148068921376768 Gaia DR3 6636090334814214528 ...                     --
0.0033616678530916998 1636148068921376768 Gaia DR3 6636090339112400000 ...                     --
0.0038498801828703495 1636148068921376768 Gaia DR3 6636090339113063296 ...                     --
                 ...                 ...                          ... ...                    ...             ...
 0.019751317240143573 1636148068921376768 Gaia DR3 6636090407832546944 ...                 0.1176           MARCS
 0.019916769172899054 1636148068921376768 Gaia DR3 6636066940132132352 ...                     --
 0.019967388048343956 1636148068921376768 Gaia DR3 6636089514478677504 ...                     --
 0.020149893249057697 1636148068921376768 Gaia DR3 6636066871411763968 ...                 0.0197         PHOENIX
Length = 50 rows
```

Queries return a limited number of rows controlled by `Gaia.ROW_LIMIT`. To change the default behaviour set this appropriately.

```
>>> Gaia.ROW_LIMIT = 8
>>> r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
INFO: Query finished. [astroquery.utils.tap.core]
>>> r.pprint(max_width=140)
         dist             solution_id             designation          ... ebpminrp_gspphot_lower ebpminrp_gspphot_upper libname_gspphot
                                                                 ...        mag                    mag
--------------------- ------------------- ---------------------------- ... ---------------------- ---------------------- ---------------
0.0026043272506261527 1636148068921376768 Gaia DR3 6636090334814214528 ...                     --                     --
0.0033616678530916998 1636148068921376768 Gaia DR3 6636090339112400000 ...                     --                     --
0.0038498801828703495 1636148068921376768 Gaia DR3 6636090339113063296 ...                     --                     --
 0.004422603920589843 1636148068921376768 Gaia DR3 6636090339112213760 ...                     --                     --
 0.004545515007418226 1636148068921376768 Gaia DR3 6636090334814217600 ...                 0.0007                 0.0079           MARCS
  0.00561391998241014 1636148068921376768 Gaia DR3 6636089583198816640 ...                 0.0064                 0.0385           MARCS
 0.005845777923125324 1636148068921376768 Gaia DR3 6636090334814218752 ...                     --                     --
 0.006210490970134131 1636148068921376768 Gaia DR3 6636090334814213632 ...                     --                     --
```

To return an unlimited number of rows set `Gaia.ROW_LIMIT` to -1.

```
>>> Gaia.ROW_LIMIT = -1
>>> r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
INFO: Query finished. [astroquery.utils.tap.core]
>>> r.pprint(max_lines=12, max_width=140)
         dist             solution_id             designation          ... ebpminrp_gspphot_lower ebpminrp_gspphot_upper libname_gspphot
                                                                 ...        mag                    mag
--------------------- ------------------- ---------------------------- ... ---------------------- ---------------------- ---------------
0.0026043272506261527 1636148068921376768 Gaia DR3 6636090334814214528 ...                     --                     --
0.0033616678530916998 1636148068921376768 Gaia DR3 6636090339112400000 ...                     --                     --
0.0038498801828703495 1636148068921376768 Gaia DR3 6636090339113063296 ...                     --                     --
                ...                ...                        ... ...                    ...                    ...             ...
  0.05121116044832183 1636148068921376768 Gaia DR3 6636065840618481024 ...                     --                     --
 0.051956798257063855 1636148068921376768 Gaia DR3 6636093637644158592 ...                     --                     --
  0.05321040019668312 1636148068921376768 Gaia DR3 6633086847005369088 ...                 0.0003                 0.0043           MARCS
Length = 184 rows
```

#### 1.2. Cone search

This query performs a cone search centered at the specified RA/Dec coordinates with the provided
radius argument.

```
>>> import astropy.units as u
>>> from astropy.coordinates import SkyCoord
>>> from astroquery.gaia import Gaia
>>>
>>> Gaia.ROW_LIMIT = 50  # Ensure the default row limit.
>>> coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
>>> j = Gaia.cone_search_async(coord, radius=u.Quantity(1.0, u.deg))
INFO: Query finished. [astroquery.utils.tap.core]
>>> r = j.get_results()
>>> r.pprint()
    solution_id             designation          ...          dist
                                               ...
------------------- ---------------------------- ... ---------------------
1636148068921376768 Gaia DR3 6636090334814214528 ... 0.0026043272506261527
1636148068921376768 Gaia DR3 6636090339112400000 ... 0.0033616678530916998
1636148068921376768 Gaia DR3 6636090339113063296 ... 0.0038498801828703495
1636148068921376768 Gaia DR3 6636090339112213760 ...  0.004422603920589843
                         ... ...                   ...
1636148068921376768 Gaia DR3 6636090407832546944 ...  0.019751317240143573
1636148068921376768 Gaia DR3 6636066940132132352 ...  0.019916769172899054
1636148068921376768 Gaia DR3 6636089514478677504 ...  0.019967388048343956
1636148068921376768 Gaia DR3 6636066871411763968 ...  0.020149893249057697
Length = 50 rows
```

#### 1.4. Synchronous query

The results of a synchronous query are stored at the user side (i.e., they are not saved in the
server). These queries must be used when the amount of data to be retrieved (number of rows)
is small, otherwise, a timeout error can be raised (an error created because the execution
time of the query exceeds time execution limit; see here [archive\_tips](https://www.cosmos.esa.int/web/gaia/faqs) for details). The output
of the synchronous queries is limited to 2000 rows. If you need more than that, you must use
asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

```
>>> from astroquery.gaia import Gaia
>>> job = Gaia.launch_job("select top 100 "
...                       "solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al, "
...                       "matched_transits,duplicated_source,phot_variable_flag "
...                       "from gaiadr3.gaia_source order by source_id")
>>> r = job.get_results()
>>> print(r['ra_dec_corr'])
ra_dec_corr
------------
  0.12293493
  0.16325329
   0.1152631
  0.03106277
 0.090631574
  0.25799984
  0.15041357
  0.15176746
  0.19033876
  0.18675442
         ...
  0.03700819
-0.047490653
  0.18519369
  0.11701631
  0.14461127
  0.05615686
  0.26646927
-0.019807748
  0.81679803
 -0.07291612
 -0.12864673
Length = 100 rows
```

Query saving results in a file (you may use ‘output\_format’ to specified the results data format,
available formats are: ‘votable’, ‘votable\_plain’, ‘fits’, ‘csv’ and ‘json’, default is ‘votable’):

```
>>> from astroquery.gaia import Gaia
>>> job = Gaia.launch_job("select top 100 "
...                       "solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al, "
...                       "matched_transits,duplicated_source,phot_variable_flag "
...                       "from gaiadr3.gaia_source order by source_id",
...                       dump_to_file=True, output_format='votable')
>>> print(job.outputFile)
1668863838419O-result.vot.gz
>>> r = job.get_results()
>>> print(r['solution_id'])
  solution_id
-------------------
1635721458409799680
1635721458409799680
1635721458409799680
1635721458409799680
1635721458409799680
              ...
Length = 100 rows
```

Note: you can inspect the status of the job by typing:

```
>>> print(job)
<Table length=100>
        name          dtype  unit                     description
-------------------- ------- ---- ---------------------------------------------------
         solution_id   int64                                      Solution Identifier
           ref_epoch float64   yr                                     Reference epoch
         ra_dec_corr float32      Correlation between right ascension and declination
astrometric_n_obs_al   int32                          Total number of observations AL
matched_observations   int16            Amount of observations matched to this source
   duplicated_source    bool                            Source with duplicate sources
  phot_variable_flag  object                             Photometric variability flag
Jobid: None
Phase: COMPLETED
Owner: None
Output file: 1668864127567O-result.vot.gz
Results: None
```

#### 1.5. Synchronous query on an ‘on-the-fly’ uploaded table

A votable can be uploaded to the server in order to be used in a query.

You have to provide the local path to the file you want to upload. In the following example,
the file ‘my\_table.xml’ is located to the relative location where your python program is running. See note below.

```
>>> from astroquery.gaia import Gaia
>>> upload_resource = 'my_table.xml'
>>> j = Gaia.launch_job(query="select * from tap_upload.table_test",
... upload_resource=upload_resource, upload_table_name="table_test", verbose=True)
>>> r = j.get_results()
>>> r.pprint()
source_id alpha delta
--------- ----- -----
        a   1.0   2.0
        b   3.0   4.0
        c   5.0   6.0
```

Note: to obtain the current location, type:

```
>>> import os
>>> print(os.getcwd())
/Current/directory/path
```

#### 1.6. Asynchronous query

Asynchronous queries save results at server side and depends on the user files quota.
These queries can be accessed at any time. For anonymous users, results are kept for three days.

Queries retrieved results can be stored locally in memory (by default) or in a file.

Query without saving results in a file:

```
>>> from astroquery.gaia import Gaia
>>> job = Gaia.launch_job_async("select top 100 designation,ra,dec "
...                             "from gaiadr3.gaia_source order by source_id")
INFO: Query finished. [astroquery.utils.tap.core]
>>> r = job.get_results()
>>> print(r)
     designation               ra                 dec
                              deg                 deg
---------------------- ------------------ --------------------
   Gaia DR3 4295806720  44.99615537864534 0.005615226341865997
  Gaia DR3 34361129088  45.00432028915398 0.021047763781174733
  Gaia DR3 38655544960 45.004978371745516 0.019879675701858644
 Gaia DR3 309238066432  44.99503714416301  0.03815169755425531
              ...
Length = 100 rows
```

Query saving results in a file (you may use ‘output\_format’ to specified the results data format,
available formats are: ‘votable’, ‘votable\_plain’, ‘fits’, ‘csv’ and ‘json’, default is ‘votable’):

```
>>> from astroquery.gaia import Gaia
>>> job = Gaia.launch_job_async("select top 100 ra, dec "
...                             "from gaiadr3.gaia_source order by source_id",
...                             dump_to_file=True, output_format='votable')
>>> print(job)
Jobid: 1611860482314O
Phase: COMPLETED
Owner: None
Output file: 1611860482314O-result.vot.gz
Results: None
```

#### 1.7. Asynchronous job removal

To remove asynchronous jobs:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.remove_jobs(["job_id_1","job_id_2",...])
```

### 2. Authenticated access

Authenticated users are able to access to TAP+ capabilities (shared tables, persistent jobs, etc.)
In order to authenticate a user, `login` or `login_gui` methods must be called. After a
successful login, the user will be authenticated until `logout` method is called.

All previous methods (`query_object`, `cone_search`, `load_table`, `load_tables`, `launch_job`) explained for
non authenticated users are applicable for authenticated ones.

The main differences are:

#### 2.1. Login/Logout

There are several ways to login to Gaia archive.

**Login through graphic interface**

*Note: Python Tkinter module is required to use login\_gui method.*

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login_gui()
```

**Login through command line**

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login(user='userName', password='userPassword')
```

**Login through a credentials file**

A file where the credentials are stored can be used to login:

*The file must containing user and password in two different lines.*

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login(credentials_file='my_credentials_file')
```

If you do not provide any parameters at all, a prompt will ask for the user name and password:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> User: user
>>> Password: pwd (not visible)
```

To logout:

#### 2.2. Listing shared tables

In the Gaia archive user tables can be shared among user groups.

To obtain a list of the tables shared to a user type the following:

```
>>> from astroquery.gaia import Gaia
>>> tables = Gaia.load_tables(only_names=True, include_shared_tables=True)
INFO: Retrieving tables... [astroquery.utils.tap.core]
INFO: Parsing tables... [astroquery.utils.tap.core]
INFO: Done. [astroquery.utils.tap.core]
>>> for table in (tables):
...   print(table.get_qualified_name())
external.apassdr9
external.gaiadr2_astrophysical_parameters
external.gaiadr2_geometric_distance
external.gaiaedr3_distance
  ...     ...       ...
tap_schema.key_columns
tap_schema.keys
tap_schema.schemas
tap_schema.tables
```

#### 2.3. Uploading table to user space

It is now possible to store a table in the private user space. The table to be uploaded can
be in a [VOTable](https://www.ivoa.net/documents/VOTable/) located in a given URL, a table stored in a local file in the user machine,
a pre-computed Astropy table file or a job executed in the Gaia archive.

Each user has a database schema described as: ‘user\_<user\_login\_name>’. For instance, if a
login name is ‘joe’, the database schema is ‘user\_joe’. Your uploaded table can be
referenced as ‘user\_joe.table\_name’

#### 2.3.1. Uploading table from URL

An already generated VOTable, accessible through a URL, can be uploaded to Gaia archive.

The following example launches a query to Vizier TAP (‘url’ parameter). The result is a
VOTable that can be uploaded to the user private area.

Your schema name will be automatically added to the provided table name:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> # Provide a URL pointing to valid VOTable resource
>>> url = ("https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync/?"
...        "REQUEST=doQuery&lang=ADQL&FORMAT=votable&"
...        "QUERY=select+*+from+TAP_SCHEMA.columns+where+table_name='II/336/apass9'")
>>> job = Gaia.upload_table(upload_resource=url, table_name="table_test_from_url",
... table_description="Some description")
Job '1539932326689O' created to upload table 'table_test_from_url'.
```

Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user\_<your\_login\_name>.<table\_name>*. Note that if the <table\_name> contains capital letters, it must be
surrounded by quotation marks, i.e.: *user\_<your\_login\_name>.”<table\_name>”*):

```
>>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_url'
>>> query = 'select * from ' + full_qualified_table_name
>>> job = Gaia.launch_job(query=query)
>>> results = job.get_results()
```

#### 2.3.2. Uploading table from file

A file containing a table can be uploaded to the user private area. Only a file associated to any of the formats described in
<https://docs.astropy.org/en/stable/io/unified.html#built-in-table-readers-writers>, and automatically identified by its suffix
or content can be used. Note that for a multi-extension fits file with multiple tables, the first table found will be used.
For any other format, the file can be transformed into an astropy Table (<https://docs.astropy.org/en/stable/io/unified.html#getting-started-with-table-i-o>)
and passed to the method.

The parameter ‘format’ must be provided when the input file is not a votable file.

Your schema name will be automatically added to the provided table name.

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> job = Gaia.upload_table(upload_resource="1535553556177O-result.vot",
...                         table_name="table_test_from_file", format="VOTable")

Sending file: 1535553556177O-result.vot
Uploaded table 'table_test_from_file'.
```

Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user\_<your\_login\_name>.<table\_name>*. Note that if the <table\_name> contains capital letters, it must be
surrounded by quotation marks, i.e.: *user\_<your\_login\_name>.”<table\_name>”*):

```
>>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_file'
>>> query = 'select * from ' + full_qualified_table_name
>>> job = Gaia.launch_job(query=query)
>>> results = job.get_results()
```

#### 2.3.3. Uploading table from an astropy Table

A in memory PyTable (See <https://wiki.python.org/moin/PyTables>) can be uploaded to the user private area.

Your schema name will be automatically added to the provided table name.

```
>>> from astroquery.gaia import Gaia
>>> from astropy.table import Table
>>> a=[1,2,3]
>>> b=['a','b','c']
>>> table = Table([a,b], names=['col1','col2'], meta={'meta':'first table'})
>>> # Upload
>>> Gaia.login()
>>> Gaia.upload_table(upload_resource=table, table_name='table_test_from_astropy')
```

Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user\_<your\_login\_name>.<table\_name>*. Note that if the <table\_name> contains capital letters, it must be
surrounded by quotation marks, i.e.: *user\_<your\_login\_name>.”<table\_name>”*):

```
>>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_astropy'
>>> query = 'select * from ' + full_qualified_table_name
>>> job = Gaia.launch_job(query=query)
>>> results = job.get_results()
```

#### 2.3.4. Uploading table from job

The results generated by an *asynchronous* job (from a query executed in the Gaia archive) can be
ingested in a table in the user private area.

The following example generates a job in the Gaia archive and then, the results are ingested in a
table named: user\_<your\_login\_name>.’t’<job\_id>:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> j1 = Gaia.launch_job_async("select top 10 * from gaiadr3.gaia_source")
>>> Gaia.upload_table_from_job(job=j1)
Created table 't1539932994481O' from job: '1539932994481O'.
```

Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user\_<your\_login\_name>.”t<job\_id>”*. Note that the previous table name must be
surrounded by quotation marks since it contains capital letters.):

```
>>> full_qualified_table_name = 'user_<your_login_name>."t1710251325268O"'
>>> query = 'select * from ' + full_qualified_table_name
>>> job = Gaia.launch_job(query=query)
>>> results = job.get_results()
```

#### 2.4. Deleting table

A table from the user private area can be deleted as follows:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login_gui()
>>> job = Gaia.delete_user_table(table_name="table_test_from_file")
Table 'table_test_from_file' deleted.
```

#### 2.6. Cross match

It is possible to run a geometric cross-match between the RA/Dec coordinates of two tables using the crossmatch function
provided by the archive. To do so, the user must be logged in. This is necessary as the cross-match process will create
a join table within the user’s private space. That table includes the identifiers from both tables and the angular
separation, in degrees, between the RA/Dec coordinates of each source in the first table and its corresponding source
in the second table.

The cross-match requires 3 steps:

1. Update the user table metadata to flag the positional RA/Dec columns using the dedicated method
[`update_user_table`](../api/astroquery.utils.tap.TapPlus.html#astroquery.utils.tap.TapPlus.update_user_table "astroquery.utils.tap.core.TapPlus"), as both tables must have defined RA and Dec columns. See
previous section to learn how to assign those flags;

2. Launch the built-in cross-match method [`cross_match`](../api/astroquery.gaia.GaiaClass.html#astroquery.gaia.GaiaClass.cross_match "astroquery.gaia.GaiaClass.cross_match"), which creates a table in the user’s
private area;

3. Subsequently, this table can be employed to retrieve the data from both tables, launching an ADQL query with the
“launch\_job” or “launch\_job\_async” method.

The following example uploads a table and then, the table is used in a cross match:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> table = file or astropy.table
>>> Gaia.upload_table(upload_resource=table, table_name='my_sources')
>>> # the table will be uploaded into the user private space into the database
>>> # the table can be referenced as <database user schema>.<table_name>
>>> full_qualified_table_name = 'user_<your_login_name>.my_sources'
>>> xmatch_table_name = 'xmatch_table'
>>> job = Gaia.cross_match(full_qualified_table_name_a=full_qualified_table_name,
...                  full_qualified_table_name_b='gaiadr3.gaia_source',
...                  results_table_name=xmatch_table_name, radius=1.0)
```

The cross-match launches an asynchronous query that saves the results at the user’s private area, so it depends on the
user files quota. This table only contains 3 columns: first table column id, second table column id and the angular
separation (degrees) between each source. Once you have your cross match finished, you can access to this table:

```
>>> xmatch_table = 'user_<your_login_name>.' + xmatch_table_name
>>> query = (f"SELECT c.separation*3600 AS separation_arcsec, a.*, b.* FROM gaiadr3.gaia_source AS a, "
...          f"{full_qualified_table_name} AS b, {xmatch_table} AS c WHERE c.gaia_source_source_id = a.source_id AND "
...          f"c.my_sources_my_sources_oid = b.my_sources_oid")
>>> job = Gaia.launch_job(query=query)
>>> results = job.get_results()
```

Cross-matching catalogues is one of the most popular operations executed in the Gaia archive.

The previous 3-step cross-match can be executed in one step by the following method:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> job = Gaia.cross_match_basic(table_a_full_qualified_name=full_qualified_table_name, table_a_column_ra='raj2000',
                     table_a_column_dec='dej2000', table_b_full_qualified_name='gaiadr3.gaia_source',
                     table_b_column_ra='ra', table_b_column_dec='dec, radius=1.0, background=True):
>>> print(job)
Jobid: 1611860482314O
Phase: COMPLETED
Owner: None
Output file: 1611860482314O-result.vot.gz
Results: None
>>> result = job.get_results()
```

This method updates the user table metadata to flag the positional RA/Dec columns and launches the positional
cross-match as an asynchronous query. Unlike the previous 3-step cross-match method, the returned job provides direct
access to the output of the cross-match information: for each matched source, all the columns from the input tables plus
the angular distance (degrees). Therefore, the size of the output can be quite large.

By default, this method targets the main catalogue of the Gaia DR3 (“gaiadr3.gaia\_source”) using a cone search radius
of 1.0 arcseconds. Therefore, the above example can also be simplified as follows:

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> job = Gaia.cross_match_basic(table_a_full_qualified_name=full_qualified_table_name, table_a_column_ra='raj2000',
                                 table_a_column_dec='dej2000')
>>> result = job.get_results()
```

#### 2.7. Tables sharing

It is possible to share tables with other users. You have to create a group, populate that
group with users, and share your table to that group. Then, any user belonging to that group
will be able to access to your shared table in a query.

#### 2.7.1. Creating a group

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> Gaia.share_group_create(group_name="my_group", description="description")
```

#### 2.7.2. Removing a group

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> Gaia.share_group_delete(group_name="my_group")
```

#### 2.7.3. Listing groups

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> groups = Gaia.load_groups()
>>> for group in groups:
...     print(group.title)
```

#### 2.7.4. Adding users to a group

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> Gaia.share_group_add_user(group_name="my_group",user_id="<user_login_name")
```

#### 2.7.5. Removing users from a group

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> Gaia.share_group_delete_user(group_name="my_group",user_id="<user_login_name>")
```

#### 2.7.6. Sharing a table to a group

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> Gaia.share_table(group_name="my_group",
...                  table_name="user_<user_login_name>.my_table",
...                  description="description")
```

#### 2.7.7. Stop sharing a table

```
>>> from astroquery.gaia import Gaia
>>> Gaia.login()
>>> Gaia.share_table_stop(table_name="user_<user_login_name>.my_table", group_name="my_group")
```