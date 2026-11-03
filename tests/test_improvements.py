"""Completion, scheduled hours, and durable recurring history regression."""
from datetime import date
from mahwar.db import Store

def payload(title="مهمة", recurrence="none", when="2026-11-04 21:35:00"):
    return dict(title=title,description="",project="شخصي",size="small",
                priority="normal",due_at=when,remind_at=when,
                recurrence=recurrence)

def test_completion_is_visible_and_reversible(tmp_path):
    db=Store(tmp_path/"done.db")
    db.save_task(payload())
    key=db.tasks()[0]["id"]
    db.toggle(key)
    assert db.tasks()[0]["done"] == 1
    assert not db.pending_reminders()
    db.toggle(key)
    assert db.tasks()[0]["done"] == 0
    db.close()

def test_recurring_task_keeps_done_occurrence_and_creates_next(tmp_path):
    db=Store(tmp_path/"recurring.db")
    db.save_task(payload(recurrence="weekly"))
    old=db.tasks()[0]
    db.toggle(old["id"])
    old_row=next(t for t in db.tasks() if t["id"]==old["id"])
    next_row=next(t for t in db.tasks() if t["id"]!=old["id"])
    assert old_row["done"] == 1
    assert old_row["due_at"] == "2026-11-04 21:35:00"
    assert next_row["done"] == 0
    assert next_row["due_at"] == "2026-11-11 21:35:00"
    assert next_row["remind_at"] == "2026-11-11 21:35:00"
    db.close()

def test_time_persists_and_end_of_day_inclusive(tmp_path):
    db=Store(tmp_path/"time.db")
    db.save_task(payload(when="2026-11-04 23:59:59"))
    rows=db.tasks(start="2026-11-04 00:00:00",end="2026-11-04 23:59:59")
    assert len(rows)==1
    assert rows[0]["due_at"].endswith("23:59:59")
    db.close()
