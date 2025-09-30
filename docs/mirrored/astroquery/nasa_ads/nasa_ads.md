```
>>> from astroquery import nasa_ads as na
# if you don't store your token as an environment variable
# or in a file, give it here
>>> na.ADS.TOKEN = 'your-token-goes-here'
# by default, the top 10 records are returned, sorted in
# reverse chronological order. This can be changed
# change the number of rows returned
>>> na.ADS.NROWS = 20
# change the sort order
>>> na.ADS.SORT = 'bibcode desc'
# change the fields that are returned (enter as strings in a list)
>>> na.ADS.ADS_FIELDS = ['author','title','abstract','pubdate']
# the "^" makes ADS to return only papers where Persson
# is first author
>>> results = na.ADS.query_simple('^Persson Origin of water around deeply embedded low-mass protostars')
>>> results[0].title
# to sort after publication date
>>> results.sort(['pubdate'])
#  get the title of the last hit
>>> title = results[-1]['title'][0]
# printout the authors of the last hit
>>> print(results[-1]['author'])
```