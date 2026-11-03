"""Qt GUI smoke test on Windows CI."""
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication
from mahwar.ui import MainWindow, TaskDialog
from mahwar.db import Store

def test_all_pages_and_form(tmp_path):
    app=QApplication.instance() or QApplication([])
    window=MainWindow(Store(tmp_path/"test.db"))
    for route in ("dashboard","week","tasks","reminders","focus","review","settings"):
        window.navigate(route)
        assert window.current==route
    dialog=TaskDialog(parent=window)
    dialog.title.setText("تجربة")
    assert dialog.payload()["title"]=="تجربة"
    dialog.close()
    window.alarm_timer.stop()
    window.focus_timer.stop()
    if window.tray: window.tray.hide()
    window.store.close()
    window.deleteLater()
