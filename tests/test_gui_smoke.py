"""Qt GUI smoke test on Windows CI."""
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from datetime import date
from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import QApplication, QLabel
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
    dialog.due.setDate(QDate(2026, 11, 4))
    dialog.at_time.setTime(QTime(16, 45))
    assert dialog.payload()["title"]=="تجربة"
    assert dialog.payload()["due_at"]=="2026-11-04 16:45:00"
    assert window.nav_scroll.widget() is not None
    assert window.today_label.text() == date.today().isoformat()
    assert not any("بياناتك محفوظة" in x.text() for x in window.findChildren(QLabel))
    dialog.close()
    window.alarm_timer.stop()
    window.focus_timer.stop()
    if window.tray: window.tray.hide()
    window.store.close()
    window.deleteLater()
