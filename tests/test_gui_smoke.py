"""Qt GUI smoke test on Windows CI."""
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from datetime import date, datetime
from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QFrame, QSizePolicy
from mahwar.ui import MainWindow, TaskDialog, CompletionBox, ModernCombo, format_due_12h, format_local_clock, format_local_date, format_local_time, greeting_for_time
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
    assert str(date.today().year) in window.today_label.text()
    assert ":" not in window.today_label.text()
    assert ":" in window.clock_label.text()
    assert "AM" in window.clock_label.text() or "PM" in window.clock_label.text()
    assert window.today_label.wordWrap() is False
    assert window.clock_label.wordWrap() is False
    assert window.today_label.layoutDirection() == Qt.RightToLeft
    assert window.clock_label.layoutDirection() == Qt.LeftToRight
    assert window.today_label.sizePolicy().horizontalPolicy() == QSizePolicy.Fixed
    assert window.clock_label.sizePolicy().horizontalPolicy() == QSizePolicy.Fixed
    assert window.clock_label.textFormat() == Qt.PlainText
    assert window.today_label.textFormat() == Qt.PlainText
    assert greeting_for_time(datetime(2026, 11, 4, 7)) == "صباح الإنجاز يبدأ بخطة واضحة"
    assert greeting_for_time(datetime(2026, 11, 4, 17)) == "مساء الإنجاز يبدأ بخطة واضحة"
    assert format_local_clock(datetime(2026, 11, 4, 17, 28, 6)).endswith("05:28:06 PM")
    assert format_local_date(datetime(2026, 11, 4, 17, 28, 6)) == "الأربعاء، 4 نوفمبر 2026"
    assert format_local_time(datetime(2026, 11, 4, 17, 28, 6)) == "05:28:06 PM"
    # Narrow window layout must not wrap AM/PM to the next line.
    window.resize(1050, 720)
    window.show()
    app.processEvents()
    assert window.clock_label.height() < 35
    assert window.today_label.height() < 35
    assert not any("بياناتك محفوظة" in x.text() for x in window.findChildren(QLabel))
    window.week_anchor = date.today()
    window.navigate("week")
    assert len(window.week_day_cards) == 7
    assert all(card.minimumWidth() >= 300 for card in window.week_day_cards.values())
    assert not any(card.maximumWidth() == 240 for card in window.week_day_cards.values())
    dialog.close()
    window.alarm_timer.stop()
    window.focus_timer.stop()
    if window.tray: window.tray.hide()
    window.store.close()
    window.deleteLater()
