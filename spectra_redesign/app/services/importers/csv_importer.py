"""Import spectra from CSV files.

This importer reads comma‑separated values files with at least two columns
representing the independent variable (e.g. wavelength) and the dependent
variable (e.g. absorbance).  Lines beginning with a '#' character are
treated as comments and skipped.  Units may be specified in the header row
after the column names in parentheses, e.g. 'wavelength_nm(nm), absorbance'.

The importer produces a Spectrum object with the parsed data and infers
units when possible.  Additional metadata such as comment lines are
stored in the Spectrum's metadata.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple
import numpy as np

from ..spectrum import Spectrum


class CsvImporter:
    """Read spectral data from CSV files."""

    def read(self, path: Path) -> Spectrum:
        """Parse the given CSV file and return a Spectrum.

        Args:
            path: Path to the CSV file.

        Returns:
            A Spectrum instance containing the data and inferred units.
        """
        comments = []
        with path.open('r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Separate comments and data lines
        data_lines = []
        for ln in lines:
            if ln.startswith('#'):
                comments.append(ln[1:].strip())
            else:
                data_lines.append(ln)

        if not data_lines:
            raise ValueError(f"No data found in {path}")

        header = data_lines[0].split(',')
        if len(header) < 2:
            raise ValueError("CSV must have at least two columns")
        x_name = header[0].strip()
        y_name = header[1].strip()

        # Extract units from names if present e.g. wavelength_nm(nm)
        def parse_name(name: str) -> Tuple[str, str]:
            if '(' in name and name.endswith(')'):
                base, unit = name[:-1].split('(', 1)
                return base.strip(), unit.strip()
            return name, ''

        x_label, x_unit = parse_name(x_name)
        y_label, y_unit = parse_name(y_name)

        # Load numeric values
        data = np.genfromtxt(data_lines[1:], delimiter=',', dtype=float)
        if data.ndim == 1:
            # Only one row of data; convert to two‑dimensional
            data = data.reshape(1, -1)
        x = data[:, 0]
        y = data[:, 1]

        metadata = {
            "comments": comments,
            "x_label": x_label,
            "y_label": y_label
        }

        return Spectrum(x=x, y=y, x_unit=x_unit or 'nm', y_unit=y_unit or 'absorbance', metadata=metadata)