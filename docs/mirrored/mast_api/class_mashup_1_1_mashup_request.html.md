Handles Mashup requests to the STScI servers.
[More...](class_mashup_1_1_mashup_request.html#details)

|  |  |
| --- | --- |
|  | |
| string | [service](class_mashup_1_1_mashup_request.html#a0efc6308190f132f13f6e480badac057) `[get, set]` |
|  | (required) The [service](_services.html) that will be queried for data [More...](#a0efc6308190f132f13f6e480badac057) |
|  | |
| IDictionary< string, object > | [params](class_mashup_1_1_mashup_request.html#abebc0aa7107f8d97168264f6d585813a) `[get, set]` |
|  | (required) Service specific parameters. [More...](#abebc0aa7107f8d97168264f6d585813a) |
|  | |
| string | [format](class_mashup_1_1_mashup_request.html#ab45c0f21d5f99662e9fc1eee3bef8b2f) `[get, set]` |
|  | (default âextjsâ) Defines the format in which dataset data will be returned. [More...](#ab45c0f21d5f99662e9fc1eee3bef8b2f) |
|  | |
| object | [data](class_mashup_1_1_mashup_request.html#a988c2eb15fd290708ba884f7b129cef8) `[get, set]` |
|  | (optional) service dependent [More...](#a988c2eb15fd290708ba884f7b129cef8) |
|  | |
| string | [filename](class_mashup_1_1_mashup_request.html#a796dd5b0cc100f026f2c6504ebd3e1b4) `[get, set]` |
|  | (optional) Filename in which to save results. [More...](#a796dd5b0cc100f026f2c6504ebd3e1b4) |
|  | |
| string | [timeout](class_mashup_1_1_mashup_request.html#a15f2ebbecad76b76b74b5a9d235e92e3) `[get, set]` |
|  | (default 20) Request timeout. [More...](#a15f2ebbecad76b76b74b5a9d235e92e3) |
|  | |
| string | [clearcache](class_mashup_1_1_mashup_request.html#a658aa290bff2947487fcc6cddf0f703d) `[get, set]` |
|  | (default false) Clear cache prior to request. [More...](#a658aa290bff2947487fcc6cddf0f703d) |
|  | |
| string | [removecache](class_mashup_1_1_mashup_request.html#a6ecbf12a4d69a175601f45e1d9caecae) `[get, set]` |
|  | (default false) Clear cache after request. [More...](#a6ecbf12a4d69a175601f45e1d9caecae) |
|  | |
| string | [removenullcolumns](class_mashup_1_1_mashup_request.html#a13184e62eec51c7fa34798a30e8457f6) `[get, set]` |
|  | (default false) Remove columns with all null values. [More...](#a13184e62eec51c7fa34798a30e8457f6) |
|  | |
| string | [page](class_mashup_1_1_mashup_request.html#a62fb34735c8ec8e683263619fa8c9a6c) `[get, set]` |
|  | (default 1) Page of results to be returned. [More...](#a62fb34735c8ec8e683263619fa8c9a6c) |
|  | |
| string | [pagesize](class_mashup_1_1_mashup_request.html#acb0bf2f4c807422144d80fa9ce45603c) `[get, set]` |
|  | (default 1000) Number of rows per page. [More...](#acb0bf2f4c807422144d80fa9ce45603c) |
|  | |

Handles Mashup requests to the STScI servers.

The Mashup Request Url is https://mast.stsci/api/v0/invoke?request=(Mashup Request Object)

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.clearcache | | getset |

(default false) Clear cache prior to request.

On incoming request, if there is a previously completed identical request (service and params match) in the server cache, if clearecache is true it is removed, if it is false cached result is returned.

|  |  |  |
| --- | --- | --- |
| |  | | --- | | object Mashup.MashupRequest.data | | getset |

(optional) service dependent

Used for uploading content to the service. Unnecessary for most services, ones that require this value will be marked (for API use crossmatch is the only important one).

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.filename | | getset |

(optional) Filename in which to save results.

If specified, the result is saved to this filename and a url to the file (on STScI servers) is returned instead.

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.format | | getset |

(default âextjsâ) Defines the format in which dataset data will be returned.

The options are: extjs, votable, csv, json (see descriptions [here](md_result_formats.html)). Almost all requests will return a dataset, however other result types are possible, in which case this property has no effect. The documentation for specific services specifies the result type.

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.page | | getset |

(default 1) Page of results to be returned.

Relevant for dataset return type only. Specifies which page of results is returned.

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.pagesize | | getset |

(default 1000) Number of rows per page.

Relevant for dataset return type only. Specifies pagesize in number of rows. Note, will not have an effect unless "page" property is also defined.

|  |  |  |
| --- | --- | --- |
| |  | | --- | | IDictionary<string, object> Mashup.MashupRequest.params | | getset |

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.removecache | | getset |

(default false) Clear cache after request.

If set to true, after a completed query is returned the result is removed from server cache.

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.removenullcolumns | | getset |

(default false) Remove columns with all null values.

Relevant for dataset return type only. If set to true, any columns with all null values are removed from the dataset.

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.service | | getset |

(required) The [service](_services.html) that will be queried for data

For example Mast.Caom.Cone. Detailed descriptions of available services are [here](_services.html).

|  |  |  |
| --- | --- | --- |
| |  | | --- | | string Mashup.MashupRequest.timeout | | getset |

(default 20) Request timeout.

This value defines the maximum number of seconds before a response is returned to the client. After timeout seconds, if the request has not completed a response of âexecutingâ is returned. At this point another request must be sent to the server for the client to receive the completed response and return data. There is a 10 minute inactivity timeout (not configurable) after which if another request has not been received by the server, the job is terminated and the server cache cleared.

---

The documentation for this class was generated from the following file: