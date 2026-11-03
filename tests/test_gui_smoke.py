"""Qt GUI smoke test on Windows CI."""
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from datetime import date
from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from mahwar.ui import MainWindow, TaskDialog, CompletionBox, ModernCombo, format_due_12h
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
    dialog.set_selected_time(QTime(16, 45))
    assert dialog.meridiem.currentData() == "PM"
    assert dialog.hour.currentData() == 4
    assert dialog.minute.currentData() == 45
    assert dialog.payload()["title"]=="تجربة"
    assert dialog.payload()["due_at"]=="2026-11-04 16:45:00"
    dialog.set_selected_time(QTime(0, 5))
    assert dialog.hour.currentData() == 12
    assert dialog.meridiem.currentData() == "AM"
    assert dialog.payload()["due_at"] == "2026-11-04 00:05:00"
    dialog.set_selected_time(QTime(12, 0))
    assert dialog.meridiem.currentData() == "PM"
    assert dialog.payload()["due_at"] == "2026-11-04 12:00:00"
    assert all(isinstance(w, ModernCombo) for w in (dialog.size, dialog.priority, dialog.recurrence))
    assert format_due_12h("2026-11-04 16:45:00").endswith("04:45 PM")
    assert window.nav_scroll.widget() is not None
    assert window.brand_header.objectName() == "BrandContainer"
    window.store.save_task(dict(title="فحص الإنجاز", description="", project="شخصي",
                                size="small", priority="normal", due_at=date.today().isoformat()+" 08:15:00",
                                remind_at="", recurrence="none"))
    window.navigate("dashboard")
    checkboxes = window.findChildren(CompletionBox)
    assert checkboxes, "The dashboard must render square checkboxes for tasks"
    checkbox = checkboxes[0]
    task_id = window.store.tasks()[0]["id"]
    checkbox.setChecked(True)
    assert next(t for t in window.store.tasks() if t["id"] == task_id)["done"] == 1
    assert not any(b.objectName() == "DoneAction" for b in window.findChildren(QPushButton))
    assert window.today_label.text() == date.today().isoformat()
    assert not any("بياناتك محفوظة" in x.text() for x in window.findChildren(QLabel))
    dialog.close()
    window.alarm_timer.stop()
    window.focus_timer.stop()
    if window.tray: window.tray.hide()
    window.store.close()
    window.deleteLater()
