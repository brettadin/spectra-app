"""Unit conversion utilities for spectra.

The `UnitsService` centralises all unit handling in the application.  Its
methods perform idempotent transformations between canonical internal units
and various user‑facing representations.  Conversions are always derived
from the original data; they do not mutate the underlying arrays.  See
`specs/units_and_conversions.md` for details on supported units and
conversion formulas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, Any
import numpy as np

@dataclass
class UnitsService:
    """Perform conversions between spectral units."""

    def convert(self, spectrum: "Spectrum", x_unit: str, y_unit: str) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Convert the given spectrum into the desired units.

        This method returns new arrays and metadata without modifying the
        input spectrum.  If conversion is not necessary, the original arrays
        are returned.  Unsupported unit combinations raise a `ValueError`.

        Args:
            spectrum: The input Spectrum object.
            x_unit: Requested unit for the x axis.
            y_unit: Requested unit for the y axis.

        Returns:
            (new_x, new_y, new_metadata): A tuple containing the converted
            independent array, dependent array and updated metadata.
        """
        from .spectrum import Spectrum  # avoid circular import at module level

        x = spectrum.x
        y = spectrum.y
        metadata = dict(spectrum.metadata)  # shallow copy

        # Convert x units
        if spectrum.x_unit != x_unit:
            x = self._convert_wavelength(x, spectrum.x_unit, x_unit)
            metadata["x_conversion"] = f"{spectrum.x_unit}→{x_unit}"

        # Convert y units
        if spectrum.y_unit != y_unit:
            y = self._convert_intensity(y, spectrum.y_unit, y_unit)
            metadata["y_conversion"] = f"{spectrum.y_unit}→{y_unit}"

        return x, y, metadata

    def _convert_wavelength(self, data: np.ndarray, src: str, dst: str) -> np.ndarray:
        """Convert wavelengths between nm, um and wavenumber (cm^-1)."""
        # canonical baseline is nm
        if src == dst:
            return data.copy()
        # convert source to nm
        if src == "nm":
            nm = data
        elif src in ["µm", "um"]:
            nm = data * 1e3
        elif src in ["cm^-1", "1/cm", "wavenumber"]:
            # wavenumber (cm^-1) → nm: λ (nm) = 1e7 / ν~ (cm^-1)
            nm = 1e7 / data
        else:
            raise ValueError(f"Unsupported source x unit: {src}")
        # convert nm to destination
        if dst == "nm":
            return nm
        elif dst in ["µm", "um"]:
            return nm / 1e3
        elif dst in ["cm^-1", "1/cm", "wavenumber"]:
            return 1e7 / nm
        else:
            raise ValueError(f"Unsupported destination x unit: {dst}")

    def _convert_intensity(self, data: np.ndarray, src: str, dst: str) -> np.ndarray:
        """Convert intensity between absorbance and transmittance.

        For demonstration, assume baseline intensity is absorbance (A), and
        transmittance (T) is related by T = 10^{-A}.  These formulas follow
        the logic in the original codebase's `ir_units.py`【328409478188748†L22-L59】.
        Additional intensity types can be added here.
        """
        if src == dst:
            return data.copy()
        if src == "absorbance" and dst == "transmittance":
            # T = 10^-A
            return 10 ** (-data)
        if src == "transmittance" and dst == "absorbance":
            # A = -log10(T)
            return -np.log10(data)
        raise ValueError(f"Unsupported conversion from {src} to {dst}")