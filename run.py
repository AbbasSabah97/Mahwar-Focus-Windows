"""Windows executable entrypoint: only one app and tray icon per Windows user."""
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from mahwar.instance import SingleInstanceCoordinator
from mahwar.ui import MainWindow
from mahwar.db import Store

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("مِحور Focus")
    app.setOrganizationName("Mahwar")
    coordinator = SingleInstanceCoordinator()
    try:
        if not coordinator.claim_or_activate():
            return 0
    except RuntimeError as exc:
        QMessageBox.critical(None, "مِحور Focus", str(exc))
        return 1
    window = MainWindow(Store())
    coordinator.activated.connect(window.restore_window)
    window.show()
    result = app.exec()
    coordinator.close()
    return result

if __name__ == "__main__":
    raise SystemExit(main())
