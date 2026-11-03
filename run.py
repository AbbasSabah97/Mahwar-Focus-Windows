"""Windows executable entrypoint."""
import sys
from PySide6.QtWidgets import QApplication
from mahwar.ui import MainWindow
from mahwar.db import Store

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("مِحور Focus")
    app.setOrganizationName("Mahwar")
    window = MainWindow(Store())
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
