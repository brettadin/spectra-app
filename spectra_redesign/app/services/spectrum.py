"""Representation of a single spectrum.

The `Spectrum` class encapsulates the independent variable (e.g. wavelength,
wavenumber) and dependent variable (e.g. absorbance, transmittance) arrays
along with associated metadata.  This object is immutable; any operation
that would alter the data produces a new instance.  Metadata about the
source file, units and provenance should be preserved at all times.

Attributes:
    x (numpy.ndarray): The independent variable array (e.g. wavelength in nm).
    y (numpy.ndarray): The dependent variable array (e.g. absorbance).
    x_unit (str): Unit of the independent variable.
    y_unit (str): Unit of the dependent variable.
    metadata (dict): Arbitrary metadata about the spectrum (instrument
        information, file headers, etc.).

Note:
    This is a simple dataclass for demonstration.  In the final application
    additional attributes may be added (e.g. error bars), and validation
    logic may be extended.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any
import numpy as np


@dataclass(frozen=True)
class Spectrum:
    """A single spectral dataset with units and metadata."""

    x: np.ndarray
    y: np.ndarray
    x_unit: str = "nm"
    y_unit: str = "absorbance"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_units(self, x_unit: str, y_unit: str, units_service: "UnitsService") -> "Spectrum":
        """Return a new Spectrum converted into the requested units.

        Conversion is delegated to the provided UnitsService instance.  If the
        requested units are the same as the current units, the same data is
        returned.  Otherwise the service performs the appropriate
        transformation and returns a new Spectrum instance.

        Args:
            x_unit: Desired unit for the x axis (e.g. 'cm^-1').
            y_unit: Desired unit for the y axis (e.g. 'transmittance').
            units_service: Service used to perform unit conversions.

        Returns:
            A new Spectrum in the requested units.
        """
        new_x, new_y, new_metadata = units_service.convert(self, x_unit, y_unit)
        return Spectrum(x=new_x, y=new_y, x_unit=x_unit, y_unit=y_unit, metadata=new_metadata)