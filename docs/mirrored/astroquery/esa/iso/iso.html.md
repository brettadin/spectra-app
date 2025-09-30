```
>>> from astroquery.esa.iso import ISO
>>> import urllib.request
>>> from astropy.io import fits
>>> from astropy import units as u
>>> import numpy as np
>>> from matplotlib import pyplot as plt
>>> from astropy.visualization import quantity_support
>>> from specutils import Spectrum1D
>>>
>>> # Search for M31 spectra
>>> table=ISO.query_ida_tap(query="SELECT target_name, ra, dec, " +
...                               "axes, units, reference FROM ivoa.ssap " +
...                               "WHERE " +
...                               "INTERSECTS(CIRCLE('ICRS',10.68470833,41.26875," +
...                               "0.08333333333333333)," +
...                               "s_region_fov)=1")
>>> table.pprint_all()
            target_name                   ra        dec       axes      units                                          reference
------------------------------------ ------------ -------- --------- ------------ -----------------------------------------------------------------------------------
ISO SWS01 Spectrum Target: M31_BULGE      10.6917 41.26997 WAVE FLUX        um Jy http://nida.esac.esa.int/nida-sl-tap/data?RETRIEVAL_TYPE=STANDALONE&obsno=400015010
ISO LWS01 Spectrum Target: M31_BULGE  10.69170999 41.26998 WAVE FLUX um W/cm^2/um http://nida.esac.esa.int/nida-sl-tap/data?RETRIEVAL_TYPE=STANDALONE&obsno=580021020
      ISO LWS01 Spectrum Target: M31 10.684999995 41.26902 WAVE FLUX um W/cm^2/um http://nida.esac.esa.int/nida-sl-tap/data?RETRIEVAL_TYPE=STANDALONE&obsno=580020010
     ISO LWS01 Spectrum Target: M31N     10.80459 41.38386 WAVE FLUX um W/cm^2/um http://nida.esac.esa.int/nida-sl-tap/data?RETRIEVAL_TYPE=STANDALONE&obsno=602020050
>>> # Download using the ISO astroquery module
>>> ISO.download_data('58002102', retrieval_type="STANDALONE", filename="58002102")
>>>
>>> # Download using the SSAP table URL invocation (both are equivalent)
>>> urllib.request.urlretrieve('http://nida.esac.esa.int/nida-sl-tap/data?' +
...                            'RETRIEVAL_TYPE=STANDALONE&obsno=580020010',
...                            '58002102.fits')
('58002102.fits', <http.client.HTTPMessage object at 0x11a6a3fd0>)
>>> # Opening the spectral fits file using astropy modules
>>> quantity_support()
<astropy.visualization.units.quantity_support.<locals>.MplQuantityConverter object at 0x11c1a9d60>
>>> f = fits.open('58002102.fits')
>>> f.info()
Filename: 58002102.fits
No.    Name      Ver    Type      Cards   Dimensions   Format
0    PRIMARY      1 PrimaryHDU      37   ()
1                 1 TableHDU        39   958R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
2                 1 TableHDU        39   962R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
3                 1 TableHDU        39   962R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
4                 1 TableHDU        39   961R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
5                 1 TableHDU        39   958R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
6                 1 TableHDU        39   961R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
7                 1 TableHDU        39   959R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
8                 1 TableHDU        39   959R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
9                 1 TableHDU        39   959R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
10                1 TableHDU        39   962R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
11                1 TableHDU        39   963R x 8C   [F8.4, E11.3, E11.3, I2, I2, I2, I2, A42]
>>> # The spectrum is in the first HDU of this file.
>>> specdata = f[1].data
>>> f.close()
>>> lamb = specdata['WAVE']  * u.um
>>> flux = specdata['FLUX']  * u.Unit('W cm-2 um-1')
>>> spec = Spectrum1D(spectral_axis=lamb, flux=flux)
>>> plt.ion()
>>> f, ax = plt.subplots()
>>> ax.step(spec.spectral_axis, spec.flux)
[<matplotlib.lines.Line2D object at 0x1204e5190>]
```