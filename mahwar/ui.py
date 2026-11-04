"""Mahwar Focus: Arabic RTL desktop interface for Windows."""
from __future__ import annotations
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QDateTime, QDate, QTime, QSize, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QAction, QCloseEvent, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QPlainTextEdit, QComboBox, QCheckBox,
    QDateTimeEdit, QDateEdit, QTimeEdit, QAbstractSpinBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QScrollArea,
    QMessageBox, QFileDialog, QSystemTrayIcon, QMenu, QProgressBar, QSpinBox, QSizePolicy,
)
from .db import Store
from .icons import icon_for

BG = "#F2F2F2"
NAVY = "#424359"
PRIMARY = "#3E8C6F"
SECONDARY = "#618C7C"
MINT = "#B4D9CB"
BORDER = "#DEE7E3"
DAY_NAMES = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
MONTH_NAMES = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

def format_local_date(now=None):
    """Arabic date, kept in a dedicated right-to-left widget."""
    now = now or datetime.now()
    return f"{DAY_NAMES[now.weekday()]}، {now.day} {MONTH_NAMES[now.month - 1]} {now.year}"


def format_local_time(now=None):
    """12-hour local time, kept in a dedicated left-to-right widget."""
    now = now or datetime.now()
    return now.strftime("%I:%M:%S %p")


def format_local_clock(now=None):
    """Plain-text helper for reports; UI uses separate direction-isolated widgets."""
    now = now or datetime.now()
    return format_local_date(now) + " | " + format_local_time(now)

def greeting_for_time(now=None):
    """Daypart switches at noon, independently of dashboard navigation."""
    now = now or datetime.now()
    return "صباح الإنجاز يبدأ بخطة واضحة" if now.hour < 12 else "مساء الإنجاز يبدأ بخطة واضحة"

ROUTES = [
    ("dashboard", "الرئيسية"), ("week", "المخطط الأسبوعي"),
    ("tasks", "جميع المهام"), ("reminders", "التذكيرات"),
    ("focus", "التركيز"), ("review", "المراجعة الأسبوعية"),
    ("settings", "الإعدادات"),
]
QSS = """
QMainWindow, QWidget { background: #F2F2F2; color: #424359; font-family: 'Segoe UI', 'Tahoma', sans-serif; font-size: 14px; }
QLabel#PageTitle { font-size: 27px; font-weight: 700; }
QLabel#Brand { color: #3E8C6F; font-size: 25px; font-weight: 800; }
QLabel#StatNumber { color: #3E8C6F; font-size: 28px; font-weight: 700; }
QLabel#Section { font-size: 18px; font-weight: 700; }
QLabel#Muted { color: #618C7C; }
QLabel#HeaderDate { color: #618C7C; font-size: 12px; background: transparent; }
QLabel#HeaderTime { color: #424359; font-size: 12px; font-weight: 700; background: transparent; }
QLabel#HeaderSeparator { color: #A6C3B8; font-size: 13px; background: transparent; }
QFrame#Card { border: 1px solid #DEE7E3; background: white; border-radius: 15px; }
QFrame#Card QLabel, QFrame#Card QCheckBox { background: transparent; }
QFrame#DayCard { border: 1px solid #DEE7E3; border-radius: 16px; background: #FFFFFF; }
QFrame#TodayCard { border: 2px solid #3E8C6F; border-radius: 16px; background: #EDF6F2; }
QFrame#WeekTask { border: 1px solid #E6EEE9; border-radius: 10px; background: #FAFCFB; }
QFrame#TodayCard QLabel, QFrame#DayCard QLabel, QFrame#WeekTask QLabel, QFrame#WeekTask QCheckBox { background: transparent; }
QLabel#DayTitle { font-size: 19px; font-weight: 800; color: #424359; }
QLabel#TodayDayTitle { font-size: 19px; font-weight: 800; color: #3E8C6F; }
QLabel#WeekTaskTitle { font-size: 14px; font-weight: 650; color: #424359; }
QLabel#WeekTaskDone { font-size: 14px; color: #618C7C; text-decoration: line-through; }
QLabel#WeekCount { background: #E2F0EA; color: #28654E; padding: 5px 10px; border-radius: 9px; }
QPushButton#SmallAction { border: none; background: transparent; color: #3E8C6F; padding: 4px 8px; font-size: 12px; text-align: right; }
QPushButton#SmallAction:hover { background: #DCECE5; }
QPushButton#AddDay { border: 1px dashed #9BC9B3; background: #F0F8F4; color: #2B6D54; padding: 8px; font-weight: 700; }
QPushButton#AddDay:hover { background: #DBEFE5; }
QPushButton { border: 1px solid #DEE7E3; border-radius: 9px; background: white; color: #424359; padding: 9px 13px; font-weight: 600; }
QPushButton:hover { border-color: #3E8C6F; background: #E9F4F0; }
QPushButton#Primary { background: #3E8C6F; border: 1px solid #3E8C6F; color: white; }
QPushButton#Primary:hover { background: #618C7C; }
QPushButton#Nav { min-height: 30px; text-align: right; border: 1px solid transparent; border-radius: 13px; background: transparent; padding: 11px 17px; font-size: 14px; font-weight: 650; }
QPushButton#Nav:hover { background: #E7F1EC; color: #3E8C6F; }
QPushButton#Nav[active="true"] { background: #B4D9CB; color: #265D49; font-weight: 800; border-color: #B4D9CB; }
QFrame#Sidebar { background: #FFFFFF; border-left: 1px solid #DEE7E3; }
QWidget#NavArea { background: #FFFFFF; }
QWidget#BrandContainer, QWidget#BrandContainer QLabel { background: transparent; border: none; }
QLabel#DoneTitle { color: #618C7C; text-decoration: line-through; }
QScrollBar:vertical { background: #F2F2F2; width: 10px; margin: 3px 2px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #B4D9CB; min-height: 35px; border-radius: 5px; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:vertical:pressed { background: #618C7C; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: #F2F2F2; height: 9px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #B4D9CB; min-width: 36px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QPushButton#Danger { color: #B84040; }
QLineEdit, QPlainTextEdit, QDateTimeEdit, QDateEdit, QTimeEdit, QComboBox, QSpinBox { background: white; border: 1px solid #DEE7E3; border-radius: 7px; padding: 7px; color: #424359; min-height: 24px; }
QComboBox { padding-right: 12px; padding-left: 32px; min-height: 30px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: left center; width: 31px; border: none; background: #EDF5F1; border-top-left-radius: 6px; border-bottom-left-radius: 6px; }
QComboBox::down-arrow { image: none; width: 0px; height: 0px; }
QComboBox:hover::drop-down { background: #DCEBE4; }
QComboBox QAbstractItemView { background: white; color: #424359; border: 1px solid #B4D9CB; padding: 5px; outline: 0; selection-background-color: #B4D9CB; selection-color: #265D49; }
QDateEdit { padding-left: 38px; min-height: 30px; }
QDateEdit::drop-down { subcontrol-origin: padding; subcontrol-position: left center; width: 31px; border: none; background: #EDF5F1; border-top-left-radius: 6px; border-bottom-left-radius: 6px; }
QDateEdit::down-arrow, QDateEdit::up-arrow { image: none; width: 0px; height: 0px; }
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #3E8C6F; }
QProgressBar { border: none; background: #E4E8E7; border-radius: 6px; height: 12px; text-align: center; }
QProgressBar::chunk { background: #5BD9AB; border-radius: 6px; }
QScrollArea { border: none; }
QCheckBox { spacing: 7px; }
QCheckBox::indicator { width: 18px; height: 18px; }
"""

def label(text, kind=None):
    widget = QLabel(str(text))
    widget.setWordWrap(True)
    if kind:
        widget.setObjectName(kind)
    return widget

def button(text, fn, primary=False, danger=False):
    widget = QPushButton(text)
    if primary:
        widget.setObjectName("Primary")
    if danger:
        widget.setObjectName("Danger")
    widget.clicked.connect(fn)
    return widget

def card_layout(padding=16):
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(11)
    return frame, layout

def clear_layout(lay):
    while lay.count():
        item = lay.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()
        elif item.layout():
            clear_layout(item.layout())

def saturday_of(current):
    return current - timedelta(days=(current.weekday() + 2) % 7)

class SmoothScrollArea(QScrollArea):
    """Animated wheel scrolling with normal scrollbar drag and keyboard support."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_anim = QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        self._scroll_anim.setDuration(190)
        self._scroll_anim.setEasingCurve(QEasingCurve.OutCubic)
    def wheelEvent(self, event):
        direction = event.angleDelta().y()
        if not direction:
            return super().wheelEvent(event)
        bar = self.verticalScrollBar()
        start = bar.value()
        target = (self._scroll_anim.endValue()
                  if self._scroll_anim.state() == QPropertyAnimation.Running else start)
        delta = int(direction / 120 * 92)
        target = max(bar.minimum(), min(bar.maximum(), target - delta))
        self._scroll_anim.stop()
        self._scroll_anim.setStartValue(start)
        self._scroll_anim.setEndValue(target)
        self._scroll_anim.start()
        event.accept()

class ModernCombo(QComboBox):
    """Native keyboard-friendly dropdown with a custom anti-aliased chevron."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(75)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#3E8C6F"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        x = 16 if self.layoutDirection() == Qt.RightToLeft else self.width() - 16
        y = self.height() / 2
        painter.drawLine(QPointF(x - 4, y - 2), QPointF(x, y + 2))
        painter.drawLine(QPointF(x, y + 2), QPointF(x + 4, y - 2))
        painter.end()


class ModernDateEdit(QDateEdit):
    """Calendar popup without the outdated numeric spinner arrows."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setToolTip("اختر التاريخ من التقويم أو اكتبه مباشرة")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#3E8C6F"), 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        x = 16 if self.layoutDirection() == Qt.RightToLeft else self.width() - 16
        y = self.height() / 2
        painter.drawRoundedRect(QRectF(x-7, y-6, 14, 13), 2, 2)
        painter.drawLine(QPointF(x-7, y-2), QPointF(x+7, y-2))
        painter.drawLine(QPointF(x-4, y-9), QPointF(x-4, y-4))
        painter.drawLine(QPointF(x+4, y-9), QPointF(x+4, y-4))
        painter.end()


class CompletionBox(QCheckBox):
    """A clean square-only completed-state control, usable with mouse and keyboard."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("وضع علامة صح لإكمال المهمة أو إلغاء الإنجاز")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(4, 4, 20, 20)
        painter.setPen(QPen(QColor("#3E8C6F" if self.isChecked() else "#96B5A8"), 1.8))
        painter.setBrush(QColor("#3E8C6F") if self.isChecked() else QColor("#FFFFFF"))
        painter.drawRoundedRect(rect, 5, 5)
        if self.isChecked():
            painter.setPen(QPen(QColor("#FFFFFF"), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(QPointF(9, 14), QPointF(12.5, 17.5))
            painter.drawLine(QPointF(12.5, 17.5), QPointF(19, 10))
        painter.end()


def format_due_12h(value):
    """12-hour display only; durable SQLite timestamps remain 24-hour ISO."""
    try:
        time_value = datetime.fromisoformat(value)
        period = "AM" if time_value.hour < 12 else "PM"
        hour = time_value.hour % 12 or 12
        return f"{time_value:%Y-%m-%d} · {hour:02}:{time_value.minute:02} {period}"
    except (ValueError, TypeError):
        return str(value)


class TaskDialog(QDialog):
    def __init__(self, parent=None, task=None, day=None):
        super().__init__(parent)
        task = task or {}
        self.setWindowTitle("إضافة مهمة" if not task else "تعديل مهمة")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(560, 540)
        form = QFormLayout(self)
        self.title = QLineEdit(task.get("title", ""))
        self.title.setPlaceholderText("ما الذي تريد إنجازه؟")
        self.description = QPlainTextEdit(task.get("description", ""))
        self.description.setMaximumHeight(65)
        self.project = QLineEdit(task.get("project", "شخصي"))
        self.size = ModernCombo()
        for text, value in [("صغيرة","small"),("متوسطة","medium"),("كبيرة","large")]:
            self.size.addItem(text, value)
        self.priority = ModernCombo()
        for text, value in [("عادية","normal"),("مرتفعة","high"),("منخفضة","low")]:
            self.priority.addItem(text,value)
        self.due = ModernDateEdit()
        self.due.setDate(QDate.currentDate())
        self.hour = ModernCombo()
        self.minute = ModernCombo()
        self.meridiem = ModernCombo()
        for h in range(1, 13):
            self.hour.addItem(f"{h:02}", h)
        for m in range(60):
            self.minute.addItem(f"{m:02}", m)
        self.meridiem.addItem("صباحاً · AM", "AM")
        self.meridiem.addItem("مساءً · PM", "PM")
        self.hour.setToolTip("اختر الساعة من 1 إلى 12")
        self.minute.setToolTip("اختر الدقيقة من 00 إلى 59")
        self.meridiem.setToolTip("اختر صباحاً AM أو مساءً PM")
        self.set_selected_time(QTime.currentTime().addSecs(3600))
        self.time_widget = QWidget()
        self.time_widget.setObjectName("TaskTimeInput")
        time_layout = QHBoxLayout(self.time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)
        time_layout.addWidget(self.hour, 1)
        colon = QLabel(":")
        colon.setAlignment(Qt.AlignCenter)
        colon.setFixedWidth(10)
        time_layout.addWidget(colon)
        time_layout.addWidget(self.minute, 1)
        time_layout.addWidget(self.meridiem, 2)
        self.alert = QCheckBox("تفعيل التذكير عند الموعد")
        self.alert.setChecked(bool(task.get("remind_at")))
        self.recurrence = ModernCombo()
        for text, value in [("بدون تكرار","none"),("يومي","daily"),("أسبوعي","weekly"),("شهري","monthly")]:
            self.recurrence.addItem(text,value)
        if day:
            self.due.setDate(QDate.fromString(day,"yyyy-MM-dd"))
            self.set_selected_time(QTime(9, 0))
        if task:
            old = QDateTime.fromString(task.get("due_at",""),"yyyy-MM-dd HH:mm:ss")
            if old.isValid():
                self.due.setDate(old.date())
                self.set_selected_time(old.time())
            for control, key in [(self.size,"size"),(self.priority,"priority"),(self.recurrence,"recurrence")]:
                index = control.findData(task.get(key))
                if index >= 0: control.setCurrentIndex(index)
        for title, widget in [
            ("اسم المهمة",self.title),("الوصف",self.description),("المشروع",self.project),
            ("حجم المهمة",self.size),("الأولوية",self.priority),
            ("تاريخ المهمة",self.due),("الوقت (12 ساعة · AM/PM)",self.time_widget),
            ("التذكير",self.alert),("التكرار",self.recurrence)
        ]:
            form.addRow(title,widget)
        controls = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        controls.button(QDialogButtonBox.Save).setText("حفظ المهمة")
        controls.button(QDialogButtonBox.Cancel).setText("إلغاء")
        controls.accepted.connect(self.check)
        controls.rejected.connect(self.reject)
        form.addRow(controls)
    def check(self):
        if not self.title.text().strip():
            QMessageBox.warning(self,"تنبيه","اكتب عنوان المهمة أولاً")
        else:
            self.accept()
    def set_selected_time(self, value: QTime):
        """Initialize 12-hour controls from a conventional 24-hour Qt value."""
        hour = value.hour() % 12 or 12
        period = "AM" if value.hour() < 12 else "PM"
        self.hour.setCurrentIndex(self.hour.findData(hour))
        self.minute.setCurrentIndex(self.minute.findData(value.minute()))
        self.meridiem.setCurrentIndex(self.meridiem.findData(period))

    def chosen_time(self) -> QTime:
        hour = int(self.hour.currentData()) % 12
        if self.meridiem.currentData() == "PM":
            hour += 12
        return QTime(hour, int(self.minute.currentData()))

    def payload(self):
        due = self.due.date().toString("yyyy-MM-dd") + " " + self.chosen_time().toString("HH:mm") + ":00"
        return dict(title=self.title.text().strip(), description=self.description.toPlainText().strip(),
                    project=self.project.text().strip() or "شخصي",
                    size=self.size.currentData(), priority=self.priority.currentData(),
                    due_at=due, remind_at=due if self.alert.isChecked() else "",
                    recurrence=self.recurrence.currentData())

class MainWindow(QMainWindow):
    def __init__(self, store=None):
        super().__init__()
        self.store = store or Store()
        self.current = "dashboard"
        self.week_anchor = date.today()
        self.seconds_left = 25*60
        self.duration = 25*60
        self.focus_running = False
        self.focus_kind = "work"
        self.setWindowTitle("مِحور Focus | خطط · ركّز · أنجز")
        self.setMinimumSize(1050,720)
        self.resize(1380,900)
        self.setLayoutDirection(Qt.RightToLeft)
        resource = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        self.icon = QIcon(str(resource/"assets"/"mahwar.ico"))
        self.setWindowIcon(self.icon)
        self.setStyleSheet(QSS)
        outer = QWidget()
        root = QHBoxLayout(outer)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(251)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(13, 22, 13, 16)
        side_layout.setSpacing(14)
        brand = QWidget()
        brand.setObjectName("BrandContainer")
        self.brand_header = brand
        brand_row = QHBoxLayout(brand)
        brand_row.setContentsMargins(9, 0, 9, 0)
        brand_row.setSpacing(11)
        brand_icon = QLabel()
        brand_icon.setPixmap(self.icon.pixmap(39, 39))
        brand_row.addWidget(brand_icon)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        brand_text.addWidget(label("مِحور","Brand"))
        brand_text.addWidget(label("خطط · ركّز · أنجز","Muted"))
        brand_row.addLayout(brand_text, 1)
        side_layout.addWidget(brand)
        self.nav_scroll = SmoothScrollArea()
        self.nav_scroll.setObjectName("NavScroll")
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_scroll.setFrameShape(QFrame.NoFrame)
        nav_content = QWidget()
        nav_content.setObjectName("NavArea")
        nav = QVBoxLayout(nav_content)
        nav.setContentsMargins(4, 12, 4, 14)
        nav.setSpacing(9)
        self.nav_buttons = {}
        for route, title in ROUTES:
            item = QPushButton(title)
            item.setObjectName("Nav")
            item.setIcon(icon_for(route, NAVY))
            item.setIconSize(QSize(21,21))
            item.setCursor(Qt.PointingHandCursor)
            item.clicked.connect(lambda _checked=False, route=route: self.navigate(route))
            self.nav_buttons[route] = item
            nav.addWidget(item)
        nav.addStretch()
        self.nav_scroll.setWidget(nav_content)
        side_layout.addWidget(self.nav_scroll,1)
        content = QWidget()
        main = QVBoxLayout(content)
        main.setContentsMargins(24,24,24,18)
        main.setSpacing(15)
        header = QHBoxLayout()
        head = QVBoxLayout()
        head.setSpacing(5)
        self.page_heading = label("لوحة القيادة", "PageTitle")
        self.page_heading.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        head.addWidget(self.page_heading)
        self._shown_date = date.today()
        # Do not put Arabic RTL and AM/PM LTR in one wrapping QLabel.
        # Separate children keep their individual text directions and layout widths.
        meta = QHBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(9)
        self.today_label = QLabel(format_local_date())
        self.today_label.setObjectName("HeaderDate")
        self.today_label.setTextFormat(Qt.PlainText)
        self.today_label.setWordWrap(False)
        self.today_label.setLayoutDirection(Qt.RightToLeft)
        self.today_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.today_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        meta.addWidget(self.today_label)
        separator = QLabel("•")
        separator.setObjectName("HeaderSeparator")
        separator.setWordWrap(False)
        separator.setAlignment(Qt.AlignCenter)
        meta.addWidget(separator)
        self.clock_label = QLabel(format_local_time())
        self.clock_label.setObjectName("HeaderTime")
        self.clock_label.setTextFormat(Qt.PlainText)
        self.clock_label.setWordWrap(False)
        self.clock_label.setLayoutDirection(Qt.LeftToRight)
        self.clock_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.clock_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        meta.addWidget(self.clock_label)
        meta.addStretch(1)
        head.addLayout(meta)
        header.addLayout(head)
        header.addStretch()
        header.addWidget(button("＋  مهمة جديدة", lambda: self.open_task(), primary=True))
        main.addLayout(header)
        self.scroller = SmoothScrollArea()
        self.scroller.setWidgetResizable(True)
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setSpacing(16)
        self.body_layout.setAlignment(Qt.AlignTop)
        self.scroller.setWidget(self.body)
        main.addWidget(self.scroller)
        root.addWidget(sidebar)
        root.addWidget(content,1)
        self.setCentralWidget(outer)
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self.icon,self)
            self.tray.setToolTip("مِحور Focus")
            menu = QMenu()
            menu.addAction("فتح مِحور", self.restore_window)
            menu.addAction("إنهاء البرنامج",self.quit_app)
            self.tray.setContextMenu(menu)
            self.tray.activated.connect(lambda _: self.restore_window())
            self.tray.show()
        self.alarm_timer = QTimer(self)
        self.alarm_timer.timeout.connect(self.check_reminders)
        self.alarm_timer.start(20000)
        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.focus_tick)
        self.focus_timer.start(1000)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.refresh_date)
        self.clock_timer.start(1000)
        self.navigate("dashboard")
        QTimer.singleShot(700,self.check_reminders)

    def refresh_date(self):
        """Update live clock and evening greeting; rebuild only when day changes."""
        now = datetime.now()
        self.today_label.setText(format_local_date(now))
        self.clock_label.setText(format_local_time(now))
        if self.current == "dashboard" and getattr(self, "greeting_label", None) is not None:
            self.greeting_label.setText("✨ " + greeting_for_time(now))
        if now.date() != self._shown_date:
            previous_day = self._shown_date
            self._shown_date = now.date()
            if saturday_of(self.week_anchor) == saturday_of(previous_day):
                self.week_anchor = now.date()
            self.navigate(self.current)

    def refresh_date_label_only(self):
        now = datetime.now()
        self._shown_date = now.date()
        self.today_label.setText(format_local_date(now))
        self.clock_label.setText(format_local_time(now))

    def navigate(self, route):
        self.refresh_date_label_only()
        self.current = route
        names = dict(ROUTES)
        self.page_heading.setText(names[route])
        for name, item in self.nav_buttons.items():
            item.setProperty("active", "true" if name==route else "false")
            item.style().unpolish(item)
            item.style().polish(item)
            item.setIcon(icon_for(name, PRIMARY if name == route else NAVY))
        clear_layout(self.body_layout)
        self.scroller.verticalScrollBar().setValue(0)
        build = getattr(self,"render_"+route)
        build()

    def open_task(self, task=None, day=None):
        form = TaskDialog(self,task,day)
        if form.exec() == QDialog.Accepted:
            self.store.save_task(form.payload(),task["id"] if task else None)
            self.navigate(self.current)

    def remove_task(self, task_id):
        if QMessageBox.question(self,"حذف المهمة","هل تريد حذف هذه المهمة؟") == QMessageBox.Yes:
            self.store.delete(task_id)
            self.navigate(self.current)

    def toggle_task(self, task_id):
        self.store.toggle(task_id)
        self.navigate(self.current)

    def task_row(self, task, reminders=False):
        frame, box = card_layout(10)
        row = QHBoxLayout()
        done = CompletionBox()
        done.setAccessibleName("تحديد اكتمال المهمة: " + task["title"])
        done.setToolTip("ضع علامة صح عند إنجاز المهمة، أو أزلها لإعادة فتحها")
        done.setChecked(bool(task["done"]))
        done.stateChanged.connect(lambda _s, task_id=task["id"]:self.toggle_task(task_id))
        row.addWidget(done)
        text_box = QVBoxLayout()
        headline = label(task["title"], "DoneTitle" if task["done"] else ("Section" if task["priority"]=="high" else None))
        text_box.addWidget(headline)
        sizes = {"large":"كبيرة", "medium":"متوسطة", "small":"صغيرة"}
        more = "{}  ·  {}  ·  {}".format(task["project"], format_due_12h(task["due_at"]), sizes.get(task["size"],"صغيرة"))
        text_box.addWidget(label(more,"Muted"))
        row.addLayout(text_box,1)
        if reminders:
            row.addWidget(button("تأجيل 10 د", lambda _=False, key=task["id"]:self.snooze(key)))
        row.addWidget(button("تعديل",lambda _=False,t=task:self.open_task(t)))
        row.addWidget(button("حذف",lambda _=False,key=task["id"]:self.remove_task(key),danger=True))
        box.addLayout(row)
        return frame

    def add_section(self,text):
        self.body_layout.addWidget(label(text,"Section"))

    def render_dashboard(self):
        banner, banner_box = card_layout(22)
        self.greeting_label = label("✨ " + greeting_for_time(), "Section")
        banner_box.addWidget(self.greeting_label)
        banner_box.addWidget(label("اختر أهم مهمة اليوم، ونظّم أسبوعك دون ازدحام.", "Muted"))
        self.body_layout.addWidget(banner)
        stats = self.store.stats()
        row = QHBoxLayout()
        for title, value, hint in [
            ("المهام المفتوحة",stats["open"],"بانتظار التنفيذ"),
            ("إنجازات الأسبوع",stats["done"],"إجمالي المهام المكتملة"),
            ("وقت التركيز",f'{stats["minutes"]//60} س {stats["minutes"]%60} د',"هذا الأسبوع"),
            ("المهام المتأخرة",stats["overdue"],"تحتاج إلى إعادة جدولة")
        ]:
            tile, lay = card_layout()
            lay.addWidget(label(title))
            lay.addWidget(label(value,"StatNumber"))
            lay.addWidget(label(hint,"Muted"))
            row.addWidget(tile)
        self.body_layout.addLayout(row)
        section = QHBoxLayout()
        tasks_card, tasks_box = card_layout()
        tasks_box.addWidget(label("المهام المجدولة لليوم","Section"))
        today = date.today().isoformat()
        today_tasks = self.store.tasks(start=today+" 00:00:00",end=today+" 23:59:59")
        for task in today_tasks[:6]:
            tasks_box.addWidget(self.task_row(task))
        if not today_tasks:
            tasks_box.addWidget(label("لا توجد مهام اليوم. ابدأ بإضافة مهمتك الأولى.","Muted"))
        tasks_box.addStretch()
        section.addWidget(tasks_card,3)
        balance, balance_box=card_layout()
        balance_box.addWidget(label("توازن اليوم — قاعدة 1-3-5","Section"))
        for key,goal,title in [("large",1,"مهمة كبيرة"),("medium",3,"3 مهام متوسطة"),("small",5,"5 مهام صغيرة")]:
            count = sum(1 for t in today_tasks if t["size"]==key)
            balance_box.addWidget(label(f"{title} — {count}/{goal}"))
            progress=QProgressBar()
            progress.setRange(0,goal)
            progress.setValue(min(count,goal))
            progress.setTextVisible(False)
            balance_box.addWidget(progress)
        balance_box.addStretch()
        balance_box.addWidget(button("فتح المخطط الأسبوعي",lambda:self.navigate("week")))
        section.addWidget(balance,2)
        self.body_layout.addLayout(section)
        self.add_section("أولويات الأيام القادمة")
        for task in self.store.tasks(end=(date.today()+timedelta(days=7)).isoformat()+" 23:59:59")[:5]:
            if not task["done"]:
                self.body_layout.addWidget(self.task_row(task))

    def render_week(self):
        """Readable two-column weekly board; all task titles remain visible."""
        week = saturday_of(self.week_anchor)
        days = [week + timedelta(days=index) for index in range(7)]
        all_tasks = self.store.tasks(start=week.isoformat() + " 00:00:00",
                                     end=days[-1].isoformat() + " 23:59:59")
        by_day = {day.isoformat(): [] for day in days}
        for task in all_tasks:
            by_day[task["due_at"][:10]].append(task)

        header_card, header_box = card_layout(18)
        navigation = QHBoxLayout()
        week_title = label(f"الأسبوع: {days[0].strftime('%d/%m')} — {days[-1].strftime('%d/%m/%Y')}", "Section")
        navigation.addWidget(week_title, 1)
        navigation.addWidget(button("السابق", lambda: self.change_week(-7)))
        navigation.addWidget(button("هذا الأسبوع", lambda: self.change_week(0)))
        navigation.addWidget(button("التالي", lambda: self.change_week(7)))
        header_box.addLayout(navigation)
        done = sum(bool(task["done"]) for task in all_tasks)
        header_box.addWidget(label(f"المهام: {len(all_tasks)}    •    المكتملة: {done}    •    المتبقية: {len(all_tasks) - done}", "Muted"))
        self.body_layout.addWidget(header_card)

        # Two generous columns instead of seven tiny unreadable day columns.
        board = QGridLayout()
        board.setContentsMargins(0, 0, 0, 0)
        board.setHorizontalSpacing(16)
        board.setVerticalSpacing(16)
        board.setColumnStretch(0, 1)
        board.setColumnStretch(1, 1)
        self.week_day_cards = {}
        for index, day in enumerate(days):
            key = day.isoformat()
            items = by_day[key]
            frame = QFrame()
            frame.setObjectName("TodayCard" if day == date.today() else "DayCard")
            frame.setMinimumWidth(300)
            frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            day_box = QVBoxLayout(frame)
            day_box.setContentsMargins(18, 16, 18, 17)
            day_box.setSpacing(10)
            day_header = QHBoxLayout()
            title = label(DAY_NAMES[day.weekday()], "TodayDayTitle" if day == date.today() else "DayTitle")
            day_header.addWidget(title, 1)
            day_header.addWidget(label(f"{day.day:02}/{day.month:02}", "Muted"))
            if day == date.today():
                day_header.addWidget(label("اليوم", "WeekCount"))
            day_box.addLayout(day_header)
            day_box.addWidget(label(f"{len(items)} مهمة · {sum(bool(t['done']) for t in items)} مكتملة", "Muted"))

            if not items:
                nothing = label("لا توجد مهام مجدولة لهذا اليوم.", "Muted")
                nothing.setMinimumHeight(36)
                day_box.addWidget(nothing)
            else:
                for task in items:
                    item_frame = QFrame()
                    item_frame.setObjectName("WeekTask")
                    task_layout = QHBoxLayout(item_frame)
                    task_layout.setContentsMargins(10, 9, 10, 9)
                    task_layout.setSpacing(8)
                    done_check = CompletionBox()
                    done_check.setAccessibleName("إنجاز " + task["title"])
                    done_check.setChecked(bool(task["done"]))
                    done_check.stateChanged.connect(
                        lambda _state, key=task["id"]: self.toggle_task(key))
                    task_layout.addWidget(done_check, 0, Qt.AlignTop)
                    info = QVBoxLayout()
                    info.setSpacing(3)
                    task_title = label(task["title"], "WeekTaskDone" if task["done"] else "WeekTaskTitle")
                    task_title.setToolTip(task["title"])
                    info.addWidget(task_title)
                    due = datetime.fromisoformat(task["due_at"])
                    info.addWidget(label(f"{due.strftime('%I:%M %p')}  ·  {task['project']}", "Muted"))
                    task_layout.addLayout(info, 1)
                    edit = button("تعديل", lambda _=False, t=task: self.open_task(t))
                    edit.setObjectName("SmallAction")
                    task_layout.addWidget(edit, 0, Qt.AlignTop)
                    day_box.addWidget(item_frame)

            add = button("＋ إضافة مهمة", lambda _=False, d=key: self.open_task(day=d))
            add.setObjectName("AddDay")
            day_box.addWidget(add)
            board.addWidget(frame, index // 2, index % 2, Qt.AlignTop)
            self.week_day_cards[key] = frame
        self.body_layout.addLayout(board)

        goals_card, goals_box = card_layout(18)
        goals_box.addWidget(label("الأهداف الرئيسية لهذا الأسبوع", "Section"))
        for goal in self.store.goals(week.isoformat()):
            check = QCheckBox(goal["title"])
            check.setChecked(bool(goal["done"]))
            check.stateChanged.connect(lambda _, gid=goal["id"]: self.goal_toggle(gid))
            goals_box.addWidget(check)
        goal_row = QHBoxLayout()
        entry = QLineEdit()
        entry.setPlaceholderText("اكتب هدفاً لهذا الأسبوع")
        goal_row.addWidget(entry, 1)
        goal_row.addWidget(button("إضافة هدف", lambda: self.add_goal(week.isoformat(), entry.text())))
        goals_box.addLayout(goal_row)
        self.body_layout.addWidget(goals_card)

    def change_week(self, amount):
        self.week_anchor=date.today() if amount==0 else self.week_anchor+timedelta(days=amount)
        self.navigate("week")

    def add_goal(self,week,text):
        self.store.add_goal(week,text)
        self.navigate("week")

    def goal_toggle(self,goal_id):
        self.store.toggle_goal(goal_id)
        self.navigate("week")

    def render_tasks(self):
        self.search=QLineEdit()
        self.search.setPlaceholderText("بحث بالعنوان أو المشروع")
        self.search.textChanged.connect(self.refresh_task_results)
        self.body_layout.addWidget(self.search)
        self.task_results=QVBoxLayout()
        self.body_layout.addLayout(self.task_results)
        self.refresh_task_results()

    def refresh_task_results(self):
        clear_layout(self.task_results)
        rows=self.store.tasks(self.search.text())
        if not rows:
            self.task_results.addWidget(label("لا توجد مهام مطابقة.","Muted"))
        for task in rows:
            self.task_results.addWidget(self.task_row(task))

    def render_reminders(self):
        self.add_section("التذكيرات القادمة والمتأخرة")
        rows=[t for t in self.store.tasks() if t["remind_at"] and not t["done"]]
        rows.sort(key=lambda r:r["remind_at"])
        if not rows:
            self.body_layout.addWidget(label("لا توجد تذكيرات. فعّل التذكير أثناء إضافة المهمة.","Muted"))
        for task in rows:
            self.body_layout.addWidget(self.task_row(task,reminders=True))
        self.body_layout.addWidget(label("لتظهر الإشعارات يجب أن يكون مِحور قيد التشغيل أو في شريط النظام.","Muted"))

    def snooze(self,task_id):
        self.store.snooze(task_id,10)
        self.navigate(self.current)

    def render_focus(self):
        box, stack = card_layout(28)
        stack.addWidget(label("جلسة تركيز دون مشتتات","Section"))
        self.timer_label = label(self.format_focus(),"StatNumber")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 64px; font-weight: 800; color: #3E8C6F;")
        stack.addWidget(self.timer_label)
        track=QProgressBar()
        track.setRange(0,self.duration)
        track.setValue(self.duration-self.seconds_left)
        track.setTextVisible(False)
        self.focus_progress=track
        stack.addWidget(track)
        row=QHBoxLayout()
        row.addWidget(button("25 دقيقة",lambda:self.configure_focus(25)))
        row.addWidget(button("50 دقيقة",lambda:self.configure_focus(50)))
        row.addWidget(button("استراحة 5 دقائق",lambda:self.configure_focus(5,rest=True)))
        stack.addLayout(row)
        actions=QHBoxLayout()
        self.toggle_button=button("إيقاف مؤقت" if self.focus_running else "ابدأ التركيز",self.toggle_focus,primary=True)
        actions.addWidget(self.toggle_button)
        actions.addWidget(button("إعادة ضبط",self.reset_focus))
        stack.addLayout(actions)
        self.body_layout.addWidget(box)
        self.body_layout.addWidget(label("تُسجَّل جلسة التركيز عند اكتمالها فقط.","Muted"))

    def format_focus(self):
        return f"{self.seconds_left//60:02}:{self.seconds_left%60:02}"

    def configure_focus(self,minutes,rest=False):
        self.focus_running=False
        self.focus_kind="rest" if rest else "work"
        self.duration=minutes*60
        self.seconds_left=self.duration
        self.navigate("focus")

    def toggle_focus(self):
        self.focus_running=not self.focus_running
        self.toggle_button.setText("إيقاف مؤقت" if self.focus_running else "ابدأ التركيز")

    def reset_focus(self):
        self.focus_running=False
        self.seconds_left=self.duration
        self.navigate("focus")

    def focus_tick(self):
        if not self.focus_running:
            return
        self.seconds_left=max(0,self.seconds_left-1)
        if self.current=="focus":
            self.timer_label.setText(self.format_focus())
            self.focus_progress.setValue(self.duration-self.seconds_left)
        if self.seconds_left==0:
            self.focus_running=False
            if self.focus_kind=="work":
                self.store.record_session(self.duration//60)
            self.notify("انتهت جلسة التركيز" if self.focus_kind=="work" else "انتهت الاستراحة")
            if self.current=="focus":
                self.navigate("focus")

    def render_review(self):
        week=saturday_of(date.today()).isoformat()
        review=self.store.review(week)
        self.add_section(f"المراجعة الأسبوعية — {week}")
        form,lay=card_layout()
        self.review_fields={}
        for key,title in [("achievements","ما الإنجازات التي حققتها؟"),
                          ("obstacles","ما العقبات التي واجهتك؟"),
                          ("improvements","ما الذي ستحسنه الأسبوع القادم؟")]:
            lay.addWidget(label(title,"Section"))
            edit=QPlainTextEdit(review.get(key,""))
            edit.setMinimumHeight(90)
            lay.addWidget(edit)
            self.review_fields[key]=edit
        lay.addWidget(label("مستوى الطاقة (1 إلى 5)"))
        self.energy=QSpinBox()
        self.energy.setRange(1,5)
        self.energy.setValue(review.get("energy",3))
        lay.addWidget(self.energy)
        lay.addWidget(button("حفظ المراجعة",lambda:self.save_review(week),primary=True))
        self.body_layout.addWidget(form)

    def save_review(self,week):
        self.store.save_review(week,*(self.review_fields[k].toPlainText() for k in
                                     ("achievements","obstacles","improvements")),self.energy.value())
        QMessageBox.information(self,"مِحور","تم حفظ المراجعة الأسبوعية.")

    def render_settings(self):
        card,box=card_layout()
        box.addWidget(label("البيانات والخصوصية","Section"))
        box.addWidget(label("تُحفظ المهام والمراجعات في قاعدة SQLite محلية على هذا الحاسوب.","Muted"))
        box.addWidget(button("تصدير نسخة احتياطية JSON",self.backup))
        box.addWidget(button("استيراد نسخة احتياطية JSON",self.restore))
        box.addWidget(label("النسخ الاحتياطية الصادرة من هذه النسخة فقط. الاستيراد يستبدل بياناتك الحالية.","Muted"))
        box.addWidget(label("ألوان التطبيق: #424359 · #3E8C6F · #618C7C · #B4D9CB · #F2F2F2","Muted"))
        self.body_layout.addWidget(card)

    def backup(self):
        path,_=QFileDialog.getSaveFileName(self,"حفظ نسخة احتياطية","MahwarBackup.json","JSON (*.json)")
        if path:
            try:
                self.store.export_json(path)
                QMessageBox.information(self,"مِحور","تم تصدير النسخة الاحتياطية.")
            except Exception as exc:
                QMessageBox.critical(self,"خطأ",str(exc))

    def restore(self):
        path,_=QFileDialog.getOpenFileName(self,"استيراد نسخة احتياطية","","JSON (*.json)")
        if path and QMessageBox.question(self,"تأكيد","سيتم استبدال البيانات الحالية. هل تريد المتابعة؟")==QMessageBox.Yes:
            try:
                self.store.import_json(path)
                self.navigate("dashboard")
            except Exception as exc:
                QMessageBox.critical(self,"خطأ",str(exc))

    def check_reminders(self):
        for task in self.store.pending_reminders():
            self.notify(task["title"],f'حان موعد المهمة: {format_due_12h(task["due_at"])}')
            self.store.mark_notified(task["id"])
        if self.current=="reminders":
            pass

    def notify(self,title,message="مِحور Focus"):
        if self.tray:
            self.tray.showMessage(title,message,QSystemTrayIcon.Information,9000)
        else:
            QApplication.beep()

    def restore_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def quit_app(self):
        self._exit = True
        if self.tray:
            self.tray.hide()
        self.close()
        QApplication.quit()

    def closeEvent(self,event:QCloseEvent):
        if self.tray and not getattr(self,"_exit",False):
            self.hide()
            event.ignore()
            self.tray.showMessage("مِحور Focus","البرنامج يعمل في شريط النظام لاستمرار التذكيرات.",QSystemTrayIcon.Information,3000)
        else:
            self.store.close()
            event.accept()
