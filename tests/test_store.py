"""Data integrity, recurrence, backup and weekly-planner tests."""
import json
from datetime import datetime, timedelta
from mahwar.db import Store, next_occurrence
from mahwar.ui import saturday_of
from datetime import date

def sample(**kwargs):
    x=dict(title="كتابة التقرير",description="",project="العمل",size="large",
           priority="high",due_at="2026-11-04 12:00:00",remind_at="2026-11-04 12:00:00",
           recurrence="none")
    x.update(kwargs)
    return x

def test_create_edit_delete(tmp_path):
    db=Store(tmp_path/"db.sqlite")
    db.save_task(sample())
    task=db.tasks()[0]
    assert task["title"]=="كتابة التقرير"
    db.save_task(sample(title="تقرير جديد"),task["id"])
    assert db.tasks()[0]["title"]=="تقرير جديد"
    db.toggle(task["id"])
    assert db.tasks()[0]["done"]==1
    db.delete(task["id"])
    assert db.tasks()==[]
    db.close()

def test_recurrence_and_snooze(tmp_path):
    db=Store(tmp_path/"db.sqlite")
    db.save_task(sample(recurrence="daily"))
    key=db.tasks()[0]["id"]
    db.toggle(key)
    task=db.tasks()[0]
    assert task["done"]==1 and task["due_at"]=="2026-11-04 12:00:00"
    future = next(t for t in db.tasks() if not t["done"])
    assert future["due_at"]=="2026-11-05 12:00:00"
    db.snooze(key,10)
    assert db.tasks()[0]["notified"]==0
    db.close()

def test_month_end():
    assert next_occurrence("2026-01-31 08:00:00","monthly")=="2026-02-28 08:00:00"
    assert next_occurrence("2026-12-31 08:00:00","monthly")=="2027-01-31 08:00:00"

def test_week_starts_saturday():
    assert saturday_of(date(2026,11,3))==date(2026,10,31)
    assert saturday_of(date(2026,10,31))==date(2026,10,31)

def test_review_goals_backup(tmp_path):
    db=Store(tmp_path/"db.sqlite")
    db.save_review("2026-10-31","نجحت","وقت","ابدأ مبكرا",4)
    db.add_goal("2026-10-31","الهدف الأول")
    db.save_task(sample())
    assert db.review("2026-10-31")["energy"]==4
    assert len(db.goals("2026-10-31"))==1
    p=tmp_path/"backup.json"
    db.export_json(p)
    assert json.loads(p.read_text(encoding="utf8"))["application"]=="MahwarFocus"
    db.delete(db.tasks()[0]["id"])
    db.import_json(p)
    assert len(db.tasks())==1
    db.close()

def test_invalid_backup_does_not_destroy_data(tmp_path):
    db=Store(tmp_path/"db.sqlite")
    db.save_task(sample())
    p=tmp_path/"bad.json"
    p.write_text(json.dumps({"application":"OtherApp"}))
    try:
        db.import_json(p)
    except ValueError:
        pass
    else:
        assert False, "Expected backup validation"
    assert len(db.tasks())==1
    db.close()
