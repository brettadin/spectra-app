# Introduction

This page gives many examples of MAST queries using Python. Each example is fully runnable (in both python 2.x and python 3.x), but may refer to other example functions on this page. To download the file in its entirety, click [here](apiEx.py).

There is also a tutorial that can be viewed [here](MastApiTutorial.html), or downloaded as a [jupyter notebook](MastApiTutorial.ipynb).

# Includes and Helper Functions

This section contains all necessary imports for the examples given here, as well a several helper functions used throughout the page.

import sys

import os

import time

import re

import json

import requests

from urllib.parse import quote as urlencode

## MAST Query

Sends a request to the MAST server and returns the response.

def mast\_query(request):

"""Perform a MAST query.

Parameters

----------

request (dictionary): The MAST request json object

Returns head,content where head is the response HTTP headers, and content is the returned data"""

request\_url='https://mast.stsci.edu/api/v0/invoke'

version = ".".join(map(str, sys.version\_info[:3]))

headers = {"Content-type": "application/x-www-form-urlencoded",

"Accept": "text/plain",

"User-agent":"python-requests/"+version}

req\_string = json.dumps(request)

req\_string = urlencode(req\_string)

resp = requests.post(request\_url, data="request="+req\_string, headers=headers)

head = resp.headers

content = resp.content.decode('utf-8')

return head, content

## Download Request

Performs a get request to download a specified file from the MAST server.

def download\_request(payload, filename, download\_type="file"):

request\_url='https://mast.stsci.edu/api/v0.1/Download/' + download\_type

resp = requests.post(request\_url, data=payload)

with open(filename,'wb') as FLE:

FLE.write(resp.content)

return filename

## Set Query Filters

Some filtering queries require human-unfriendly syntax. This allows you to enter your filter criteria as a dictionary, which will then be parsed into correct format for searching.

def set\_filters(parameters):

return [{"paramName":p, "values":v} for p,v in parameters.items()]

## Set Min/Max Values

Some parameters require minimum and maximum acceptable values: for example, both RA and Dec must be given as a range. This is a convenience function to format such a query correctly.

def set\_min\_max(min, max):

return [{'min': min, 'max': max}]

## Convert json to csv

Converts json return type object into csv.

def mast\_json2csv(json):

csv\_str = ",".join([x['name'] for x in json['fields']])

csv\_str += "\n"

csv\_str += ",".join([x['type'] for x in json['fields']])

csv\_str += "\n"

col\_names = [x['name'] for x in json['fields']]

for row in json['data']:

csv\_str += ",".join([str(row.get(col,"nul")) for col in col\_names]) + "\n"

return csv\_str

## Convert json to astropy Table

Convets json return type object into an astropy Table.

from astropy.table import Table

import numpy as np

def mast\_json2table(json\_obj):

data\_table = Table()

for col,atype in [(x['name'],x['type']) for x in json\_obj['fields']]:

if atype=="string":

atype="str"

if atype=="boolean":

atype="bool"

data\_table[col] = np.array([x.get(col,None) for x in json\_obj['data']],dtype=atype)

return data\_table

# Name Resolver

[Mast.Name.Lookup](_services.html#MastNameLookup).  
Depends on [mast\_query](#mast_query).

def resolve\_name():

request = {'service':'Mast.Name.Lookup',

'params':{'input':'M101',

'format':'json'},

}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

# List Missions

[Mast.Missions.List](_services.html#MastMissionsList)  
Depends on [mast\_query](#mast_query).

def list\_caom\_missions():

request = {

'service':'Mast.Missions.List',

'params':{},

'format':'json'

}

headers, out\_string = mast\_query(request)

out\_data = [x['distinctValue'] for x in json.loads(out\_string)['data']]

return out\_data

# Cone Searches

## CAOM Cone Search

[Mast.Caom.Cone](_services.html#MastCaomCone).  
Depends on [mast\_query](#mast_query).  
See the [CAOM field documentation](_c_a_o_mfields.html) for information on the returned columns.

def caom\_cone\_search():

cachebreaker = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

request = {'service':'Mast.Caom.Cone',

'params':{'ra':254.28746,

'dec':-4.09933,

'radius': 0.2,

'cachebreaker': cachebreaker},

'format':'json',

'pagesize':5000,

'page':1,

'removenullcolumns':True,

'timeout':3,

'cachebreaker': cachebreaker}

status = 'EXECUTING'

while status == 'EXECUTING':

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

status = out\_data['status']

print(status)

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## VO Cone Search

[Vo.Hesarc.DatascopeListable](_services.html#VoHesarcDatascopeListable).  
Depends on [mast\_query](#incPy).  
Note that instead of returning all results at once, this query returns partial results as they become availible.

def vo\_cone\_search():

request = {'service':'Vo.Hesarc.DatascopeListable',

'params':{'ra':254.28746,

'dec':-4.09933,

'radius':0.2},

'format':'json',

'removenullcolumns':True}

all\_data = []

start\_time = time.time()

while True:

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

all\_data.append(out\_data)

if out\_data['status'] != "EXECUTING":

break

if time.time() - start\_time > 30:

print("Working...")

start\_time = time.time()

time.sleep(10)

return all\_data

## HSC V2 Cone Search

[Mast.Hsc.Db.v2](_services.html#MastHscDbv2).  
Depends on [mast\_query](#mast_query).  
See the [HSC field documentation](_h_s_cfields.html) for information on the returned columns.

def hscV2\_cone\_search():

request = {'service':'Mast.Hsc.Db.v2',

'params':{'ra':254.287,

'dec':-4.09933,

'radius':0.2,

'nr':5000,

'ni':1,

'magtype':1},

'format':'json',

'pagesize':1000,

'page':1,

'removenullcolumns':True}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## HSC V3 Cone Search

[Mast.Hsc.Db.v3](_services.html#MastHscDbv3).  
Depends on [mast\_query](#mast_query).  
See the [HSC field documentation](_h_s_cfields.html) for information on the returned columns.

def hscV3\_cone\_search():

request = {'service':'Mast.Hsc.Db.v3',

'params':{'ra':254.287,

'dec':-4.09933,

'radius':0.2,

'nr':5000,

'ni':1,

'magtype':1},

'format':'json',

'pagesize':1000,

'page':1,

'removenullcolumns':True}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## GAIA DR1 Cone Search

[Mast.Catalogs.GaiaDR1.Cone](_services.html#MastCatalogsGaiaDR1Cone).  
Depends on [mast\_query](#incPy).  
See the [Gaia field documentation](_gaiafields.html) for information on the returned columns.

def gaiaDR1\_cone\_search():

request = {'service':'Mast.Catalogs.GaiaDR1.Cone',

'params':{'ra':254.287,

'dec':-4.09933,

'radius':0.2},

'format':'json',

'pagesize':1000,

'page':5}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## GAIA DR2 Cone Search

[Mast.Catalogs.GaiaDR2.Cone](_services.html#MastCatalogsGaiaDR2Cone).  
Depends on [mast\_query](#incPy).  
See the [Gaia field documentation](_gaiafields.html) for information on the returned columns.

def gaiaDR2\_cone\_search():

request = {'service':'Mast.Catalogs.GaiaDR2.Cone',

'params':{'ra':254.287,

'dec':-4.09933,

'radius':0.2},

'format':'json',

'pagesize':1000,

'page':5}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## TGAS Cone Search

[Mast.Catalogs.Tgas.Cone](_services.html#MastCatalogsTgasCone).  
Depends on [mast\_query](#mast_query).  
See the [Gaia field documentation](_gaiafields.html) for information on the returned columns.

def tgas\_cone\_search():

request = { "service":"Mast.Catalogs.Tgas.Cone",

"params":{

"ra":254.28746,

"dec":-4.09933,

"radius":0.2},

"format":"json",

"timeout":10}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## GALEX Cone Search

[Mast.Galex.Catalog](_services.html#MastGalexCatalog).  
Depends on [mast\_query](#mast_query).  
See the [GALEX field documentation](_g_a_l_e_xfields.html) for information on the returned columns.

def galex\_cone\_search():

request = { "service":"Mast.Galex.Catalog",

"params":{

"ra":254.28746,

"dec":-4.09933,

"radius":0.2},

"format":"json",

"timeout":10}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## TIC Cone Search

[Mast.Catalogs.Tic.Cone](_services.html#MastCatalogsTicCone).  
Depends on [mast\_query](#mast_query).  
See the [TIC field documentation](_t_i_cfields.html) for information on the returned columns.

def tic\_cone\_search():

request = { "service":"Mast.Catalogs.Tic.Cone",

"params":{

"ra":254.28746,

"dec":-4.09933,

"radius":0.2},

"format":"json",

"timeout":10}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## CTL Cone Search

[Mast.Catalogs.Ctl.Cone](_services.html#MastCatalogsCtlCone).  
Depends on [mast\_query](#mast_query).  
See the [TIC/CTL field documentation](_t_i_cfields.html) for information on the returned columns.

def ctl\_cone\_search():

request = { "service":"Mast.Catalogs.Ctl.Cone",

"params":{

"ra":254.28746,

"dec":-4.09933,

"radius":0.2},

"format":"json",

"timeout":10}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## Disk Detective Cone Search

[Mast.Catalogs.DiskDetective.Cone](_services.html#MastCatalogsDiskDetectiveCone).  
Depends on [mast\_query](#mast_query).  
See the [Disk\_Detective field documentation](_disk__detectivefields.html) for information on the returned columns.

def dd\_cone\_search():

request = { "service":"Mast.Catalogs.DiskDetective.Cone",

"params":{

"ra":254.28746,

"dec":-4.09933,

"radius":0.2},

"format":"json",

"timeout":10}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

# Advanced Search

Advanced searches replicate the functionality of our search portals. To get the number of matching results, you pass the columns parameter as "columns":"COUNT\_BIG(\*)". You can return all columns using "columns":"\*". If you do not pass the columns parameter, the default is to return all columns.

## Advanced Search Filtering

[Mast.Caom.Filtered](_services.html#MastCaomFiltered).  
Depends on [mast\_query](#mast_query).  
This service allows the user to perform a counts only query, or to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
See the [CAOM field documentation](_c_a_o_mfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def advanced\_search\_counts():

request = {"service":"Mast.Caom.Filtered",

"format":"json",

"params":{

"columns":"COUNT\_BIG(\*)",

"filters":[

{"paramName":"filters",

"values":["NUV","FUV"],

"separator":";"

},

{"paramName":"t\_max",

"values":[{"min":52264.4586,"max":54452.8914}],

},

{"paramName":"obsid",

"values":[],

"freeText":"%200%"}

]}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

def advanced\_search():

filts = set\_filters({

"dataproduct\_type": ["image"],

"proposal\_pi": ["Osten"]

})

request = {"service":"Mast.Caom.Filtered",

"format":"json",

"params":{

"columns":"\*",

"filters":filts,

"obstype":"all"

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## Filtering with specified position

[Mast.Caom.Filtered.Position](_services.html#MastCaomFilteredPosition).  
Depends on [mast\_query](#mast_query).  
This service allows the user to perform a counts only query, or to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
See the [CAOM field documentation](_c_a_o_mfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def advanced\_search\_with\_position\_counts():

filts = set\_filters({"dataproduct\_type": ["cube", "image"]})

request = { "service":"Mast.Caom.Filtered.Position",

"format":"json",

"params":{

"columns":"COUNT\_BIG(\*)",

"filters":filts,

"position":"210.8023, 54.349, 5"

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

def advanced\_search\_with\_position():

filts = set\_filters({"dataproduct\_type": ["cube"]})

request = {"service":"Mast.Caom.Filtered.Position",

"format":"json",

"params":{

"columns":"\*",

"filters":filts,

"position":"210.8023, 54.349, 0.24"

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## TESS Searches

Since there are many advanced search options for TESS, they are collated into this section. Note that "CTL" refers to the TESS Candidate Target List.

### TIC Filtered Search

[Mast.Catalogs.Filtered.Tic](_services.html#MastCatalogsFilteredTic).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
This service allows the user to perform a counts only query, or to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
It is recommended to use [TIC Filtered Search (Data Only)](#MastCatalogsFilteredTicRowsPy) for downloading the results.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def tic\_advanced\_search():

filts = set\_filters({

"dec" : set\_min\_max(-90, -30),

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Tic",

"format":"json",

"params":{

"columns":"COUNT\_BIG(\*)",

"filters": filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### TIC Filtered Search (Data Only)

[Mast.Catalogs.Filtered.Tic.Rows](_services.html#MastCatalogsFilteredTicRows).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
This service allows the user to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query using [TIC Filtered Search](#MastCatalogsFilteredTicPy) to avoid memory overflow.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def tic\_advanced\_search\_rows():

filts = set\_filters({

"dec" : set\_min\_max(-90, -30),

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Tic.Rows",

"format":"json",

"params":{

"columns":"\*",

"filters": filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### TIC filtering with specified position

[Mast.Catalogs.Filtered.Tic.Position](_services.html#MastCatalogsFilteredTicPosition).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
This service allows the user to perform a counts only query, or to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
It is recommended to use [TIC filtering with specified position (Data Only)](#MastCatalogsFilteredTicPositionRowsPy) for downloading the results.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def tic\_advanced\_search\_position():

filts = set\_filters({

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Tic.Position",

"format":"json",

"params":{

"columns":"BIG\_COUNTS(\*)",

"filters": filts,

"ra": 210.8023,

"dec": 54.349,

"radius": .2

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### TIC filtering with specified position (Data Only)

[Mast.Catalogs.Filtered.Tic.Position.Rows](_services.html#MastCatalogsFilteredTicPositionRows).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
This service allows the user to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query using [TIC filtering with specified position](#MastCatalogsFilteredTicPositionPy) to avoid memory overflow.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def tic\_advanced\_search\_position\_rows():

filts = set\_filters({

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Tic.Position.Rows",

"format":"json",

"params":{

"columns":"\*",

"filters": filts,

"ra": 210.8023,

"dec": 54.349,

"radius": .2

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### CTL Filtered Search

[Mast.Catalogs.Filtered.Ctl](_services.html#MastCatalogsFilteredTic).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
This service allows the user to perform a counts only query, or to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
It is recommended to use [CTL Filtered Search (Data Only)](#MastCatalogsFilteredCtlRowsPy) for downloading the results.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def ctl\_advanced\_search():

filts = set\_filters({

"dec" : set\_min\_max(-90, -30),

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Ctl",

"format":"json",

"params":{

"columns": "COUNT\_BIG(\*)",

"filters":filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### CTL Filtered Search (Data Only)

Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
Depends on [mast\_query](#mast_query).  
This service allows the user to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query using [CTL Filtered Search](#MastCatalogsFilteredCtlPy) to avoid memory overflow.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def ctl\_advanced\_search\_rows():

filts = set\_filters({

"dec" : set\_min\_max(-90, -30),

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Ctl.Rows",

"format":"json",

"params":{

"columns": "\*",

"filters": filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### CTL filtering with specified position

[Mast.Catalogs.Filtered.Ctl.Position](_services.html#MastCatalogsFilteredCtlPosition).  
Depends on [mast\_query](#mast_query).  
This service allows the user to perform a counts only query, or to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
It is recommended to use [CTL filtering with specified position (Data Only)](#MastCatalogsFilteredCtlPositionRowsPy) for downloading the results.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def ctl\_advanced\_search\_position():

filts = set\_filters({

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Ctl.Position",

"format":"json",

"params":{

"columns":"COUNT\_BIG(\*)",

"filters": filts,

"ra": 210.8023,

"dec": 54.349,

"radius": .2

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### CTL filtering with specified position (Data Only)

[Mast.Catalogs.Filtered.Ctl.Position.Rows](_services.html#MastCatalogsFilteredCtlPositionRows).  
Depends on [mast\_query](#mast_query).  
This service allows the user to get the usual grid of results. When unsure how many results are expected, it is best to first perform a counts query using [CTL filtering with specified position](#MastCatalogsFilteredCtlPositionPy) to avoid memory overflow.  
See the [TIC field documentation](_t_i_cfields.html) for information on what columns may be filtered on and how inputs should be formatted.

def ctl\_advanced\_search\_position\_rows():

filts = set\_filters({

"Teff" : set\_min\_max(4250, 4500),

"logg" : set\_min\_max(4.4, 5.0),

"Tmag" : set\_min\_max(8, 10)

})

request = {"service":"Mast.Catalogs.Filtered.Ctl.Position.Rows",

"format":"json",

"params":{

"columns":"\*",

"filters": filts,

"ra": 210.8023,

"dec": 54.349,

"radius": .2

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## Disk Detective

These queries allow you to search the results from Disk Detective, a citizen-science search for circumstellar disks.

### Disk Detective filtered Counts

[Mast.Catalogs.Filtered.DiskDetective.Count](_services.html#MastCatalogsFilteredDiskDetectiveCount).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
This service allows the user to perform a counts only query. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
See the [Disk Detective field documentation](_disk__detectivefields.html) for information on what columns may be filtered on and how inputs should be formatted.

def dd\_advanced\_search\_counts():

filts = set\_filters({

"classifiers": set\_min\_max(10, 18),

"oval": set\_min\_max(15, 76)

})

request = {"service":"Mast.Catalogs.Filtered.DiskDetective.Count",

"format":"json",

"params":{

"filters":filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### Disk Detective filtered Counts with specified position

[Mast.Catalogs.Filtered.DiskDetective.Position.Count](_services.html#MastCatalogsFilteredDiskDetectivePositionCount).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
This service allows the user to perform a counts only query. When unsure how many results are expected, it is best to first perform a counts query to avoid memory overflow.  
See the [Disk Detective field documentation](_disk__detectivefields.html) for information on what columns may be filtered on and how inputs should be formatted.

def dd\_advanced\_search\_position\_counts():

filts = set\_filters({

"classifiers": set\_min\_max(10, 18),

})

request = {"service":"Mast.Catalogs.Filtered.DiskDetective.Position.Count",

"format":"json",

"params":{

"filters": filts,

"ra": 86.6909,

"dec": 0.079,

"radius": .2

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### Disk Detective filtered search

[Mast.Catalogs.Filtered.DiskDetective](_services.html#MastCatalogsFilteredDiskDetective).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
See the [Disk Detective field documentation](_disk__detectivefields.html) for information on what columns may be filtered on and how inputs should be formatted.

def dd\_advanced\_search():

filts = set\_filters({

"classifiers": set\_min\_max(10, 18),

"oval": set\_min\_max(15, 76)

})

request = {"service":"Mast.Catalogs.Filtered.DiskDetective",

"format":"json",

"params":{

"filters": filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### Disk Detective filtered search with specified position

[Mast.Catalogs.Filtered.DiskDetective.Position](_services.html#MastCatalogsFilteredDiskDetectivePosition).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
See the [Disk Detective field documentation](_disk__detectivefields.html) for information on what columns may be filtered on and how inputs should be formatted.

def dd\_advanced\_search\_position():

filts = set\_filters({

"classifiers": set\_min\_max(10, 18)

})

request = {"service":"Mast.Catalogs.Filtered.DiskDetective.Position",

"format":"json",

"params":{

"filters": filts,

"ra": 86.6909,

"dec": 0.079,

"radius": .2

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## Hubble Searches

It is possible to query for data taken by WFC3, both in UV and IR.

### WFC3 PSF UVIS filtered search

[Mast.Catalogs.Filtered.Wfc3Psf.Uvis](_services.html#MastCatalogsFilteredWfc3PsfUvis).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
See the [WFC3 PSF UVIS field documentation](_w_f_c3__p_s_ffields.html) for information on what columns may be filtered on and how inputs should be formatted.

def get\_wfc3uvis\_matches():

filts = set\_filters({

'psf\_x\_center': set\_min\_max(6,18),

'filter': ['F814W', 'F390W']

})

request = {"service":"Mast.Catalogs.Filtered.Wfc3Psf.Uvis",

"format":"json",

"params":{

"columns": "\*",

"filters": filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

### WFC3 PSF IR filtered search

[Mast.Catalogs.Filtered.Wfc3Psf.Ir](_services.html#MastCatalogsFilteredWfc3PsfIr).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
See the [WFC3 PSF IR field documentation](_w_f_c3__p_s_ffields.html) for information on what columns may be filtered on and how inputs should be formatted.

def get\_wfc3ir\_matches():

filts = set\_filters({

'psf\_x\_center': set\_min\_max(6,18),

'filter': ['F814W', 'F390W']

})

request = {"service":"Mast.Catalogs.Filtered.Wfc3Psf.Ir",

"format":"json",

"params":{

"columns":"\*",

"filters":filts

}}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## JWST NIRCam Filtered Search

[Mast.Jwst.Filtered.Nircam](_services.html#MastScienceInstrumentKeywordsNircam).  
Depends on [mast\_query](#mast_query), [set\_min\_max](#set_min_max), and [set\_filters](#set_filters).  
See the [JWST Instrument Keywords page](_jwst_inst_keywd.html) for all available filters and their properties. To filter by a different instrument, replace "Nircam" with "Niriss", "Nirspec", "Miri", "Fgs", "Guidestar", or "Wss". Replace COUNT\_BIG(\*) with \* to return all columns, rather than just the number of results.

def jwst\_nircam\_search():

filts = set\_filters({

'prop\_dec': set\_min\_max(0, 90),

'mu\_dec': set\_min\_max(-10, -2)

})

request = {"service":"Mast.JWST.Filtered.Nircam",

"format":"json",

"params":{

"columns":"COUNT\_BIG(\*)",

"filters":filts

}

}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

# HSC Spectra

[Mast.HscSpectra.Db.All](_services.html#MastHscSpectraDbAll).  
Depends on [mast\_query](#mast_query) and [download\_request](#download_req).  
Note that this query returns all HSC spectra held by MAST.  
See the [HSC spectra field documentation](_h_s_c__spectrafields.html) for information on the returned columns.

def hsc\_spectra\_search():

request = {'service':'Mast.HscSpectra.Db.All',

'format':'votable'}

headers, out\_string = mast\_query(request)

return out\_string

To download any of the returned spectra an access url can be constructed from the 'datasetName' field as below.

def download\_hsc\_spectra():

request = {'service':'Mast.HscSpectra.Db.All',

'format':'json'}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

for spec in out\_data['data'][:3]:

if spec['SpectrumType'] < 2:

dataurl = 'https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&dataset=' \

+ spec['DatasetName']

filename = spec['DatasetName']

else:

dataurl = 'https://hla.stsci.edu/cgi-bin/ecfproxy?file\_id=' \

+ spec['DatasetName'] + '.fits'

filename = spec['DatasetName'] + '.fits'

out\_file = download\_request(dataurl, filename)

print(out\_file)

# HSC Matches

## HSC V2 Matches

[Mast.HscMatches.Db.v2](_services.html#MastHscMatchesDbv2).  
Depends on [HSC V2 Cone Search](#MastHscDbv2Py) and [mast\_query](#mast_query).  
See the [HSC matches field documentation](_h_s_c__matchesfields.html) for information on the returned columns.

def get\_hscv2\_matches():

result = hscV2\_cone\_search()

data = result['data']

matchId = data[0]['MatchID']

request = {'service':'Mast.HscMatches.Db.v2',

'params':{'input':matchId},

'format':'json',

'page':1,

'pagesize':4}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## HSC V3 Matches

[Mast.HscMatches.Db.v3](_services.html#MastHscMatchesDbv3).  
Depends on [HSC V3 Cone Search](#MastHscDbv3Py) and [mast\_query](#mast_query).  
See the [HSC matches field documentation](_h_s_c__matchesfields.html) for information on the returned columns.

def get\_hscv3\_matches():

result = hscV3\_cone\_search()

data = result['data']

matchId = data[0]['MatchID']

request = {'service':'Mast.HscMatches.Db.v3',

'params':{'input':matchId},

'format':'json',

'page':1,

'pagesize':4}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

# Get VO Data

[Vo.Generic.Table](_services.html#VoGenericTable).  
Depends on [VO Cone Search](#VoHesarcDatascopeListablePy) and [mast\_query](#mast_query).

def get\_vo\_data():

vo\_data = vo\_cone\_search()

vo\_json = vo\_data[0]

row = json['data'][2]

url = row['tableURL']

request = {'service':'Vo.Generic.Table',

'params':{'url':url},

'format':'json',

'page':1,

'pagesize':1000}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

# Cross-Match

## CAOM Cross-Match

[Mast.Caom.Crossmatch](_services.html#MastCaomCrossmatch).  
Depends on [CAOM Cone Search](#MastCaomConePy) and [mast\_query](#mast_query).  
The top example shows how to use the output of a cone search as crossmatch input, and the bottom example shows how you can build the crossmatch input manually.

def crossmatch\_from\_cone\_search():

crossmatch\_input = caom\_cone\_search()

request = {"service":"Mast.Caom.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"s\_ra",

"decColumn":"s\_dec",

"radius":0.001

},

"pagesize":1000,

"page":1,

"format":"json",

"removecache":True}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

def crossmatch\_from\_minimal\_json():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":210.8,"dec":54.3}]}

request = {"service":"Mast.Caom.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.001

},

"pagesize":1000,

"page":1,

"format":"json",

"clearcache":True}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## GALEX Cross-Match

[Mast.Galex.Crossmatch](_services.html#MastGalexCrossmatch).  
Depends on [mast\_query](#incPy).

def galex\_crossmatch():

crossmatch\_input = {"fields":[{"name":"s\_ra","type":"float"},

{"name":"s\_dec","type":"float"}],

"data":[{"s\_ra":210.8,"s\_dec":54.3}]}

request = {"service":"Mast.Galex.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"s\_ra",

"decColumn":"s\_dec",

"radius":0.01

},

"pagesize":1000,

"page":1,

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## SDSS Cross-Match

[Mast.Sdss.Crossmatch](_services.html#MastSdssCrossmatch).  
Depends on [mast\_query](#mast_query).

def sdss\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":337.10977,"dec":30.30261}]}

request ={"service":"Mast.Sdss.Crossmatch",

"data":crossmatch\_input,

"params": {

"raColumn":"ra",

"decColumn":"dec",

"radius":0.01

},

"format":"json",

"pagesize":1000,

"page":1}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## 2MASS Cross-Match

[Mast.2Mass.Crossmatch](_services.html#Mast2MassCrossmatch).  
Depends on [mast\_query](#mast_query).

def twoMass\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":210.88447,"dec":54.332}]}

request = {"service":"Mast.2Mass.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.04

},

"pagesize":1000,

"page":1,

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## HSC 3.0, MagAper2 Cross-Match

[Mast.Hsc.Crossmatch.MagAper2v3](_services.html#MastHscCrossmatchMagAper2v3).  
Depends on [mast\_query](#mast_query).

def hscMagAper2\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":210.8,"dec":54.3}]}

request = {"service":"Mast.Hsc.Crossmatch.MagAper2v3",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.001

},

"pagesize":1000,

"page":1,

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## HSC 3.0, MagAuto Cross-Match

[Mast.Hsc.Crossmatch.MagAutov3](_services.html#MastHscCrossmatchMagAutov3).  
Depends on [mast\_query](#mast_query).

def hscMagAuto\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":210.8,"dec":54.3}]}

request = {"service":"Mast.Hsc.Crossmatch.MagAutov3",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.001

},

"pagesize":1000,

"page":1,

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## Gaia DR1 Cross-Match

[Mast.GaiaDR1.Crossmatch](_services.html#MastGaiaDR1Crossmatch).  
Depends on [mast\_query](#mast_query).

def gaiaDR1\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":210.8,"dec":54.3}]}

request = {"service":"Mast.GaiaDR1.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.1

},

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## Gaia DR2 Cross-Match

[Mast.GaiaDR2.Crossmatch](_services.html#MastGaiaDR2Crossmatch).  
Depends on [mast\_query](#mast_query).

def gaiaDR2\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":210.8,"dec":54.3}]}

request = {"service":"Mast.GaiaDR2.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.1

},

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## TGAS Cross-Match

[Mast.Tgas.Crossmatch](_services.html#MastTgasCrossmatch).  
Depends on [mast\_query](#mast_query).

def tgas\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":211.09,"dec":54.3228}]}

request = {"service":"Mast.Tgas.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.2

},

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## TIC Cross-Match

[Mast.Tic.Crossmatch](_services.html#MastTicCrossmatch).  
Depends on [mast\_query](#mast_query).

def tic\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":211.09,"dec":54.3228}]}

request = {"service":"Mast.Tic.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.2

},

"format":"json"}

headers,out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## CTL Cross-Match

[Mast.Ctl.Crossmatch](_services.html#MastTicCrossmatch).  
Depends on [mast\_query](#mast_query).

def ctl\_crossmatch():

crossmatch\_input = {"fields":[{"name":"ra","type":"float"},

{"name":"dec","type":"float"}],

"data":[{"ra":211.09,"dec":54.3228}]}

request = {"service":"Mast.Ctl.Crossmatch",

"data":crossmatch\_input,

"params":{

"raColumn":"ra",

"decColumn":"dec",

"radius":0.2

},

"format":"json"}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

# Getting CAOM Products

## List CAOM Products

[Mast.Caom.Products](_services.html#MastCaomProducts).  
Depends on [CAOM Cone Search](#MastCaomConePy) and [mast\_query](#mast_query).

def get\_caom\_products():

result = caom\_cone\_search()

data = result['data']

obsid = data[1]['obsid']

request = {'service':'Mast.Caom.Products',

'params':{'obsid':obsid},

'format':'json',

'pagesize':4,

'page':1}

headers, out\_string = mast\_query(request)

out\_data = json.loads(out\_string)

return out\_data

## Download Individual Products

Depends on [get\_caom\_products](#MastCaomProductsPy), and [download\_request](#download_req).

def download\_individual\_products():

result = get\_caom\_products()

data = result['data']

product = data[0]

local\_path = os.path.join("mastFiles", product['obs\_collection'], product['obs\_id'])

if not os.path.exists(local\_path):

os.makedirs(local\_path)

print(local\_path)

local\_path = os.path.join(local\_path, os.path.basename(product['productFilename']))

print(local\_path)

download\_filename = download\_request(product['dataURI'], filename=local\_path)

return download\_filename

## CAOM Data Products

Mast.Bundle.Request.  
Depends on [List CAOM Products](#MastCaomProductsPy), [CAOM Cone Search](#MastCaomConePy), [mast\_query](#mast_query), and [download\_request](#download_req).  
Multiple products can be downloaded at once using the MAST "bundle" endpoint.

def download\_multiple\_products():

result = get\_caom\_products()

product\_list = result['data']

url\_list = [("uri", url) for url in product\_list['dataURI'][:2]]

extension = ".tar.gz"

filename = "mastData"

bundle = download\_request(url\_list, filename=local\_path, download\_type="bundle")

return bundle