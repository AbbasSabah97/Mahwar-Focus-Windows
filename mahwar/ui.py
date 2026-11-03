"""Mahwar Focus: Arabic RTL desktop interface for Windows."""
from __future__ import annotations
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QDateTime, QDate, QTime, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QPlainTextEdit, QComboBox, QCheckBox,
    QDateTimeEdit, QDateEdit, QTimeEdit, QDialog, QDialogButtonBox, QFormLayout, QFrame, QScrollArea,
    QMessageBox, QFileDialog, QSystemTrayIcon, QMenu, QProgressBar, QSpinBox,
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
QFrame#Card { border: 1px solid #DEE7E3; background: white; border-radius: 15px; }
QFrame#Card QLabel, QFrame#Card QCheckBox { background: transparent; }
QPushButton { border: 1px solid #DEE7E3; border-radius: 9px; background: white; color: #424359; padding: 9px 13px; font-weight: 600; }
QPushButton:hover { border-color: #3E8C6F; background: #E9F4F0; }
QPushButton#Primary { background: #3E8C6F; border: 1px solid #3E8C6F; color: white; }
QPushButton#Primary:hover { background: #618C7C; }
QPushButton#Nav { min-height: 30px; text-align: right; border: 1px solid transparent; border-radius: 13px; background: transparent; padding: 11px 17px; font-size: 14px; font-weight: 650; }
QPushButton#Nav:hover { background: #E7F1EC; color: #3E8C6F; }
QPushButton#Nav[active="true"] { background: #B4D9CB; color: #265D49; font-weight: 800; border-color: #B4D9CB; }
QFrame#Sidebar { background: #FFFFFF; border-left: 1px solid #DEE7E3; }
QWidget#NavArea { background: #FFFFFF; }
QLabel#DoneTitle { color: #618C7C; text-decoration: line-through; }
QPushButton#DoneAction { background: #E3F2EC; color: #28654E; border-color: #B4D9CB; font-weight: 750; }
QPushButton#DoneAction:hover { background: #B4D9CB; }
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
QDateEdit::drop-down { width: 24px; border: none; }
QTimeEdit { min-width: 145px; }
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

class TaskDialog(QDialog):
    def __init__(self, parent=None, task=None, day=None):
        super().__init__(parent)
        task = task or {}
        self.setWindowTitle("إضافة مهمة" if not task else "تعديل مهمة")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(500, 470)
        form = QFormLayout(self)
        self.title = QLineEdit(task.get("title", ""))
        self.title.setPlaceholderText("ما الذي تريد إنجازه؟")
        self.description = QPlainTextEdit(task.get("description", ""))
        self.description.setMaximumHeight(65)
        self.project = QLineEdit(task.get("project", "شخصي"))
        self.size = QComboBox()
        for text, value in [("صغيرة","small"),("متوسطة","medium"),("كبيرة","large")]:
            self.size.addItem(text, value)
        self.priority = QComboBox()
        for text, value in [("عادية","normal"),("مرتفعة","high"),("منخفضة","low")]:
            self.priority.addItem(text,value)
        self.due = QDateEdit()
        self.due.setCalendarPopup(True)
        self.due.setDisplayFormat("yyyy-MM-dd")
        self.due.setDate(QDate.currentDate())
        self.at_time = QTimeEdit()
        self.at_time.setDisplayFormat("HH:mm")
        self.at_time.setTime(QTime.currentTime().addSecs(3600))
        self.at_time.setToolTip("اضغط على الساعات أو الدقائق واكتب القيمة، أو استخدم الأسهم لتغيير الوقت")
        self.at_time.setKeyboardTracking(False)
        self.alert = QCheckBox("تفعيل التذكير عند الموعد")
        self.alert.setChecked(bool(task.get("remind_at")))
        self.recurrence = QComboBox()
        for text, value in [("بدون تكرار","none"),("يومي","daily"),("أسبوعي","weekly"),("شهري","monthly")]:
            self.recurrence.addItem(text,value)
        if day:
            self.due.setDate(QDate.fromString(day,"yyyy-MM-dd"))
            self.at_time.setTime(QTime(9, 0))
        if task:
            old = QDateTime.fromString(task.get("due_at",""),"yyyy-MM-dd HH:mm:ss")
            if old.isValid():
                self.due.setDate(old.date())
                self.at_time.setTime(old.time())
            for control, key in [(self.size,"size"),(self.priority,"priority"),(self.recurrence,"recurrence")]:
                index = control.findData(task.get(key))
                if index >= 0: control.setCurrentIndex(index)
        for title, widget in [
            ("اسم المهمة",self.title),("الوصف",self.description),("المشروع",self.project),
            ("حجم المهمة",self.size),("الأولوية",self.priority),
            ("تاريخ المهمة",self.due),("الوقت (ساعة : دقيقة)",self.at_time),
            ("التذكير",self.alert),("التكرار",self.recurrence)
        ]:
            form.addRow(title,widget)
        controls = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        controls.accepted.connect(self.check)
        controls.rejected.connect(self.reject)
        form.addRow(controls)
    def check(self):
        if not self.title.text().strip():
            QMessageBox.warning(self,"تنبيه","اكتب عنوان المهمة أولاً")
        else:
            self.accept()
    def payload(self):
        due = self.due.date().toString("yyyy-MM-dd") + " " + self.at_time.time().toString("HH:mm") + ":00"
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
        brand.setObjectName("NavArea")
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
        self.page_heading = label("لوحة القيادة","PageTitle")
        head.addWidget(self.page_heading)
        self._shown_date = date.today()
        self.today_label = label(self._shown_date.strftime("%Y-%m-%d"),"Muted")
        head.addWidget(self.today_label)
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
        self.clock_timer.start(15000)
        self.navigate("dashboard")
        QTimer.singleShot(700,self.check_reminders)

    def refresh_date(self):
        """Refresh the date after midnight or resume, without recreating pages each tick."""
        local_today = date.today()
        if local_today != self._shown_date:
            self._shown_date = local_today
            self.today_label.setText(local_today.strftime("%Y-%m-%d"))
            self.navigate(self.current)

    def refresh_date_label_only(self):
        self._shown_date = date.today()
        self.today_label.setText(self._shown_date.strftime("%Y-%m-%d"))

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
        done = QCheckBox()
        done.setAccessibleName("مكتملة: " + task["title"])
        done.setToolTip("ضع علامة صح عند إنجاز المهمة، أو أزلها لإعادة فتحها")
        done.setChecked(bool(task["done"]))
        done.stateChanged.connect(lambda _s, task_id=task["id"]:self.toggle_task(task_id))
        row.addWidget(done)
        text_box = QVBoxLayout()
        headline = label(task["title"], "DoneTitle" if task["done"] else ("Section" if task["priority"]=="high" else None))
        text_box.addWidget(headline)
        sizes = {"large":"كبيرة", "medium":"متوسطة", "small":"صغيرة"}
        more = "{}  ·  {}  ·  {}".format(task["project"], task["due_at"][:16], sizes.get(task["size"],"صغيرة"))
        text_box.addWidget(label(more,"Muted"))
        row.addLayout(text_box,1)
        action = button("↶ إعادة فتح" if task["done"] else "✓ تم الإنجاز",
                        lambda _=False, task_id=task["id"]:self.toggle_task(task_id))
        action.setObjectName("DoneAction")
        action.setToolTip("إعادة المهمة إلى القائمة" if task["done"] else "تحديد المهمة كمكتملة")
        row.addWidget(action)
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
        banner_title = label("✨ صباح الإنجاز يبدأ بخطة واضحة", "Section")
        banner_box.addWidget(banner_title)
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
        week = saturday_of(self.week_anchor)
        navigation = QHBoxLayout()
        navigation.addWidget(label(f'الأسبوع: {week.isoformat()} — {(week+timedelta(days=6)).isoformat()}',"Section"))
        navigation.addStretch()
        navigation.addWidget(button("الأسبوع السابق",lambda:self.change_week(-7)))
        navigation.addWidget(button("هذا الأسبوع",lambda:self.change_week(0)))
        navigation.addWidget(button("الأسبوع التالي",lambda:self.change_week(7)))
        self.body_layout.addLayout(navigation)
        week_row=QHBoxLayout()
        for index in range(7):
            day=week+timedelta(days=index)
            frame, stack=card_layout(10)
            frame.setMinimumWidth(125)
            frame.setMaximumWidth(240)
            if day==date.today():
                frame.setStyleSheet("QFrame#Card {border:2px solid #3E8C6F;background:#EFF8F4;border-radius:15px;}")
            stack.addWidget(label(DAY_NAMES[day.weekday()],"Section"))
            stack.addWidget(label(day.strftime("%d/%m"),"Muted"))
            day_tasks=self.store.tasks(start=day.isoformat()+" 00:00:00",end=day.isoformat()+" 23:59:59")
            for task in day_tasks[:4]:
                task_line = QHBoxLayout()
                done = QCheckBox()
                done.setChecked(bool(task["done"]))
                done.setToolTip("إنجاز المهمة")
                done.stateChanged.connect(
                    lambda _state, key=task["id"]: self.toggle_task(key))
                task_line.addWidget(done)
                widget = button(task["title"][:24],
                                lambda _=False,t=task:self.open_task(t))
                if task["done"]:
                    widget.setStyleSheet("text-decoration: line-through; color: #618C7C;")
                task_line.addWidget(widget, 1)
                stack.addLayout(task_line)
            stack.addStretch()
            stack.addWidget(button("＋ إضافة",lambda _=False,d=day.isoformat():self.open_task(day=d)))
            week_row.addWidget(frame,1)
        self.body_layout.addLayout(week_row)
        self.add_section("الأهداف الرئيسية لهذا الأسبوع")
        for goal in self.store.goals(week.isoformat()):
            r=QHBoxLayout()
            check=QCheckBox(goal["title"])
            check.setChecked(bool(goal["done"]))
            check.stateChanged.connect(lambda _,gid=goal["id"]:self.goal_toggle(gid))
            r.addWidget(check)
            self.body_layout.addLayout(r)
        entry=QLineEdit()
        entry.setPlaceholderText("اكتب هدفاً لهذا الأسبوع")
        line=QHBoxLayout()
        line.addWidget(entry,1)
        line.addWidget(button("إضافة هدف",lambda:self.add_goal(week.isoformat(),entry.text())))
        self.body_layout.addLayout(line)

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
            self.notify(task["title"],f'حان موعد المهمة: {task["due_at"][:16]}')
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
        self._exit=True
        QApplication.quit()

    def closeEvent(self,event:QCloseEvent):
        if self.tray and not getattr(self,"_exit",False):
            self.hide()
            event.ignore()
            self.tray.showMessage("مِحور Focus","البرنامج يعمل في شريط النظام لاستمرار التذكيرات.",QSystemTrayIcon.Information,3000)
        else:
            self.store.close()
            event.accept()
