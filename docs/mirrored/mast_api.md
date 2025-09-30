The MAST API allows for queries to be performed programmatically rather than through the [Discovery Portal](https://mast.stsci.edu). This documentation describes how to create a valid MAST Query, as well as the MAST Services of interest to an API user.

Questions/Comments/Feedback: contact [archi.nosp@m.ve@s.nosp@m.tsci..nosp@m.edu](#)

## Documentation Organization

The [MashupRequest](class_mashup_1_1_mashup_request.html) class documentation provides information for properly formatting a MAST request to the mast servers.

The [Services](_services.html) documentation provides information about specific services that may be used.

The [Result Dataset Formats](md_result_formats.html) page documents possible return types.

The [Examples](pyex.html) page contains working code for various MAST Queries in Python.

There is also a [Tutorial](MastApiTutorial.html) that goes through a basic workflow from initial query to data download.

## The MAST Request Url

The MAST Request Url is https://mast.stsci.edu/api/v0/invoke?request=(MAST Request Object).   
The MAST service takes a single request argument, ?request=(MAST Request Object), a json object.  
The MAST service supports both HTTP GET and HTTP POST request types.

## The MAST Request Object

This is an example of the MAST Request Object, which is a MashupRequest Class json object. Each property is described in detail in the [MashupRequest](class_mashup_1_1_mashup_request.html) section.

```
 {'service':'Mast.Caom.Cone',
  'params':{'ra':254.28746,
            'dec':-4.09933,
            'radius':0.2},
  'format':'json',
  'pagesize':2000,
  'removenullcolumns':True,
  'timeout':30,
  'cachebreaker': '2020-02-12T0749'}
```

## A note about large queries

The maximum result size for a MAST Query is roughly 500,000 records (rows) due to server memory limits. If a query results in a larger response, it will raise a memory error. From a user perspective, the query errors out with the message "[Errno 54] Connection reset by peer." If this happens the query should be constrained (decrease the search radius, add more filtering) such that fewer records will be returned.

## Long Polling

MAST is a long polling service, whereby the client reissues the same request to get current job status. A note about polling is that you need to exactly replicate the original request parameters, including the cachebreaker if it is included. The purpose of the cachebreaker parameter is to compel a query to be executed freshly if new, but to also use the cache for an executing query while being polled.

[Privacy Policy](https://www.stsci.edu/privacy).