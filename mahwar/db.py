"""Local SQLite task database, reminders and focus-session persistence."""
from __future__ import annotations
import calendar
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def data_path():
    root = Path(os.environ.get("APPDATA") or (Path.home() / ".local" / "share")) / "MahwarFocus"
    root.mkdir(parents=True, exist_ok=True)
    return root / "mahwar.db"

def next_occurrence(value, frequency):
    day = datetime.fromisoformat(value)
    if frequency == "daily":
        day += timedelta(days=1)
    elif frequency == "weekly":
        day += timedelta(days=7)
    elif frequency == "monthly":
        year, month = day.year, day.month + 1
        if month == 13:
            year, month = year + 1, 1
        day = day.replace(year=year, month=month,
                          day=min(day.day, calendar.monthrange(year, month)[1]))
    return day.strftime("%Y-%m-%d %H:%M:%S")

class Store:
    def __init__(self, filename=None):
        self.connection = sqlite3.connect(str(filename or data_path()))
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL, description TEXT DEFAULT '',
          project TEXT DEFAULT 'شخصي', size TEXT DEFAULT 'small',
          priority TEXT DEFAULT 'normal', due_at TEXT NOT NULL,
          remind_at TEXT DEFAULT '', recurrence TEXT DEFAULT 'none',
          done INTEGER DEFAULT 0, notified INTEGER DEFAULT 0,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL,
          minutes INTEGER NOT NULL, task_id INTEGER);
        CREATE TABLE IF NOT EXISTS reviews (
          week_start TEXT PRIMARY KEY, achievements TEXT DEFAULT '',
          obstacles TEXT DEFAULT '', improvements TEXT DEFAULT '',
          energy INTEGER DEFAULT 3);
        CREATE TABLE IF NOT EXISTS goals (
          id INTEGER PRIMARY KEY AUTOINCREMENT, week_start TEXT NOT NULL,
          title TEXT NOT NULL, done INTEGER DEFAULT 0);
        """)
        self.connection.commit()

    def _one(self, query, params=()):
        return self.connection.execute(query, params).fetchone()

    def tasks(self, search="", start=None, end=None):
        sql = "SELECT * FROM tasks WHERE 1=1"
        args = []
        if search:
            sql += " AND (title LIKE ? OR project LIKE ? OR description LIKE ?)"
            args += [f"%{search}%"] * 3
        if start:
            sql += " AND due_at >= ?"
            args.append(start)
        if end:
            sql += " AND due_at < ?"
            args.append(end)
        sql += " ORDER BY done, due_at, CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END, id"
        return [dict(row) for row in self.connection.execute(sql, args).fetchall()]

    def save_task(self, data, task_id=None):
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValueError("Task title is required")
        fields = ("title", "description", "project", "size", "priority", "due_at", "remind_at", "recurrence")
        values = [data.get(k, "") for k in fields]
        if task_id:
            self.connection.execute(
                "UPDATE tasks SET " + ", ".join(f"{k}=?" for k in fields) + ", notified=0 WHERE id=?",
                [*values, task_id])
        else:
            self.connection.execute(
                "INSERT INTO tasks (" + ",".join(fields) + ",created_at) VALUES (" +
                ",".join("?" for _ in fields) + ",?)", [*values, datetime.now().isoformat(timespec="seconds")])
        self.connection.commit()

    def toggle(self, task_id):
        row = self._one("SELECT * FROM tasks WHERE id=?", (task_id,))
        if row is None:
            return
        if not row["done"] and row["recurrence"] in ("daily", "weekly", "monthly"):
            due = next_occurrence(row["due_at"], row["recurrence"])
            reminder = next_occurrence(row["remind_at"], row["recurrence"]) if row["remind_at"] else ""
            self.connection.execute("UPDATE tasks SET due_at=?,remind_at=?,notified=0 WHERE id=?",
                                    (due, reminder, task_id))
        else:
            self.connection.execute("UPDATE tasks SET done=1-done WHERE id=?", (task_id,))
        self.connection.commit()

    def delete(self, task_id):
        self.connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.connection.commit()

    def pending_reminders(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [dict(r) for r in self.connection.execute(
            "SELECT * FROM tasks WHERE done=0 AND notified=0 AND remind_at<>'' AND remind_at<=?",
            (now,)).fetchall()]

    def mark_notified(self, task_id):
        self.connection.execute("UPDATE tasks SET notified=1 WHERE id=?", (task_id,))
        self.connection.commit()

    def snooze(self, task_id, minutes=10):
        due = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
        self.connection.execute("UPDATE tasks SET remind_at=?,notified=0 WHERE id=?", (due, task_id))
        self.connection.commit()

    def record_session(self, minutes, task_id=None):
        self.connection.execute(
            "INSERT INTO sessions(started_at,minutes,task_id) VALUES (?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), int(minutes), task_id))
        self.connection.commit()

    def stats(self):
        all_tasks = self.tasks()
        start = datetime.now() - timedelta(days=datetime.now().weekday())
        week = start.date().isoformat()
        done = sum(t["done"] for t in all_tasks)
        overdue = sum(not t["done"] and t["due_at"][:10] < datetime.now().date().isoformat() for t in all_tasks)
        minutes = self._one("SELECT COALESCE(SUM(minutes),0) AS n FROM sessions WHERE started_at>=?", (week,))["n"]
        return {"open":len(all_tasks)-done, "done":done, "overdue":overdue, "minutes":minutes}

    def review(self, week_start):
        row = self._one("SELECT * FROM reviews WHERE week_start=?", (week_start,))
        return dict(row) if row else {}

    def save_review(self, week_start, achievements, obstacles, improvements, energy):
        self.connection.execute("""
          INSERT INTO reviews VALUES (?,?,?,?,?)
          ON CONFLICT(week_start) DO UPDATE SET
          achievements=excluded.achievements, obstacles=excluded.obstacles,
          improvements=excluded.improvements, energy=excluded.energy
        """, (week_start, achievements, obstacles, improvements, energy))
        self.connection.commit()

    def goals(self, week_start):
        return [dict(r) for r in self.connection.execute(
            "SELECT * FROM goals WHERE week_start=? ORDER BY id",(week_start,)).fetchall()]

    def add_goal(self, week_start, title):
        if title.strip():
            self.connection.execute("INSERT INTO goals(week_start,title) VALUES (?,?)",(week_start,title.strip()))
            self.connection.commit()

    def toggle_goal(self, goal_id):
        self.connection.execute("UPDATE goals SET done=1-done WHERE id=?", (goal_id,))
        self.connection.commit()

    def export_json(self, target):
        tables = ("tasks","sessions","reviews","goals")
        data = {"application":"MahwarFocus","version":1,"tables":{
            t:[dict(r) for r in self.connection.execute(f"SELECT * FROM {t}")] for t in tables}}
        Path(target).write_text(json.dumps(data, ensure_ascii=False, indent=2),encoding="utf-8")

    def import_json(self, source):
        data = json.loads(Path(source).read_text(encoding="utf-8"))
        if data.get("application") != "MahwarFocus" or not isinstance(data.get("tables"),dict):
            raise ValueError("Invalid backup file")
        tables = ("tasks","sessions","reviews","goals")
        with self.connection:
            for table in tables:
                records = data["tables"].get(table, [])
                if not isinstance(records,list):
                    raise ValueError("Invalid backup records")
                self.connection.execute(f"DELETE FROM {table}")
                for record in records:
                    if not isinstance(record,dict) or not record:
                        continue
                    keys = list(record)
                    allowed = {r["name"] for r in self.connection.execute(f"PRAGMA table_info({table})")}
                    if any(k not in allowed for k in keys):
                        raise ValueError("Unknown backup field")
                    query = f"INSERT INTO {table} (" + ",".join(keys) + ") VALUES (" + ",".join("?" for _ in keys) + ")"
                    self.connection.execute(query, [record[k] for k in keys])
    def close(self):
        self.connection.close()
