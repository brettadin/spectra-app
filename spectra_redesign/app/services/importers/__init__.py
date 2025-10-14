"""Importer classes for different file formats.

Importers read external file formats and produce Spectrum objects.  Each
importer should be registered via a plugin mechanism; for now, we include
a basic CSV importer as a reference implementation.
"""

from .csv_importer import CsvImporter

__all__ = ["CsvImporter"]