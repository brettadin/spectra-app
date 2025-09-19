import numpy as np

def blackbody_nm(wavelength_nm, T=5778):
    # Planck constant c2 in nm*K simplified
    c1 = 3.741771e-16  # W*m^2
    c2 = 1.4387769e7   # nm*K
    wl_m = np.array(wavelength_nm)*1e-9
    B = (2*np.pi*6.62607015e-34*(3e8)**2) / (wl_m**5 * (np.exp((6.62607015e-34*3e8)/(wl_m*1.380649e-23*T)) - 1))
    return (B / B.max()).tolist()
