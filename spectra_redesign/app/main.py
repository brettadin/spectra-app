"""Entry point for the Spectra‑Redesign application.

This module launches the PySide6 application and displays a simple main
window.  The UI is intentionally sparse – it is meant to demonstrate the
foundation upon which the full application will be built.  See the
`specs/ui_contract.md` document for a complete description of the intended
interface.
"""

from __future__ import annotations

import sys
from pathlib import Path
from PySide6 import QtWidgets

from .services import UnitsService, ProvenanceService
from .services.importers import CsvImporter


class MainWindow(QtWidgets.QMainWindow):
    """Main window with a simple file open action."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Spectra Redesign Prototype")
        self.resize(800, 600)
        self.units_service = UnitsService()
        self.prov_service = ProvenanceService()
        self.importer = CsvImporter()
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Central widget placeholder
        self.text_widget = QtWidgets.QTextEdit()
        self.text_widget.setReadOnly(True)
        self.setCentralWidget(self.text_widget)

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        open_action = QtWidgets.QAction("&Open CSV…", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        exit_action = QtWidgets.QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV",
                                                        str(Path.cwd()), "CSV Files (*.csv)")
        if path:
            try:
                spectrum = self.importer.read(Path(path))
                # Display summary in text widget
                info = [
                    f"Loaded file: {Path(path).name}",
                    f"Data points: {len(spectrum.x)}",
                    f"X unit: {spectrum.x_unit}",
                    f"Y unit: {spectrum.y_unit}",
                    f"Comments: {', '.join(spectrum.metadata.get('comments', [])) or 'None'}"
                ]
                self.text_widget.setPlainText("\n".join(info))
                # Generate a manifest and save next to the file for demonstration
                manifest = self.prov_service.create_manifest([Path(path)])
                manifest_path = Path(path).with_suffix('.manifest.json')
                self.prov_service.save_manifest(manifest, manifest_path)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()