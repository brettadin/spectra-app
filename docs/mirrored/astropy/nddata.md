```
>>> ccd2 = ccd[:200, :]
>>> ccd2.data.shape
(200, 600)
>>> ccd2.mask.shape
(200, 600)
>>> # Show the mask in a region around the cosmic ray:
>>> ccd2.mask[99:102, 299:311]
array([[False, False, False, False, False, False, False, False, False,
        False, False, False],
       [False,  True,  True,  True,  True,  True,  True,  True,  True,
         True,  True, False],
       [False, False, False, False, False, False, False, False, False,
        False, False, False]]...)
```