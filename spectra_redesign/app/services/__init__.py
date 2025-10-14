"""Service layer for the Spectra‑Redesign application.

The service layer provides core functionality that is independent of the user
interface.  It includes classes for representing spectra, converting units,
computing provenance manifests and importing various file formats.  By
separating these concerns from the UI, we make it easier to test and
maintain the application and to expose new functionality as plugins.
"""

from .spectrum import Spectrum
from .units_service import UnitsService
from .provenance_service import ProvenanceService

__all__ = ["Spectrum", "UnitsService", "ProvenanceService"]