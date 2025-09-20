# app/server/models.py
# Spectra App v1.1.4
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np

@dataclass
class NormalizedSpectrum:
    wavelength_nm: np.ndarray
    intensity: np.ndarray
    meta: Dict[str, Optional[str]] = field(default_factory=dict)
