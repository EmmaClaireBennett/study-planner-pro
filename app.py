import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

DATABASE = Path(os.getenv("STUDY_PLANNER_DB", Path(__file__).with_name("study_planner.db")))
app = FastAPI(title="Study Planner Pro", version="1.0.0")


def connect():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with closing(connect()) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
        CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, course TEXT NOT NULL, due_date TEXT NOT NULL, priority TEXT NOT NULL DEFAULT 'medium', completed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
        """)
        db.commit()


init_db()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    course: str = Field(min_length=1, max_length=80)
    due_date: date
    priority: Literal["low", "medium", "high"] = "medium"


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    course: str | None = Field(default=None, min_length=1, max_length=80)
    due_date: date | None = None
    priority: Literal["low", "medium", "high"] | None = None
    completed: bool | None = None


def serialize(row):
    item = dict(row)
    item["completed"] = bool(item["completed"])
    return item


@app.get("/")
def root():
    return {"name": "Study Planner Pro", "docs": "/docs"}


@app.get("/tasks")
def list_tasks(course: str | None = None, completed: bool | None = None, priority: str | None = Query(default=None, pattern="^(low|medium|high)$")):
    query = "SELECT * FROM tasks WHERE 1=1"
    values = []
    if course:
        query += " AND lower(course) = lower(?)"; values.append(course)
    if completed is not None:
        query += " AND completed = ?"; values.append(int(completed))
    if priority:
        query += " AND priority = ?"; values.append(priority)
    query += " ORDER BY due_date ASC, id DESC"
    with closing(connect()) as db:
        return [serialize(row) for row in db.execute(query, values).fetchall()]


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    with closing(connect()) as db:
        cursor = db.execute("INSERT INTO tasks(title,course,due_date,priority,created_at) VALUES(?,?,?,?,?)", (task.title, task.course, task.due_date.isoformat(), task.priority, datetime.now(timezone.utc).isoformat()))
        db.commit()
        return serialize(db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone())


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    fields = update.model_dump(exclude_unset=True)
    if "due_date" in fields and fields["due_date"]:
        fields["due_date"] = fields["due_date"].isoformat()
    if "completed" in fields:
        fields["completed"] = int(fields["completed"])
    if not fields:
        raise HTTPException(400, "Provide at least one field to update")
    assignments = ", ".join(f"{key} = ?" for key in fields)
    with closing(connect()) as db:
        cursor = db.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", [*fields.values(), task_id])
        if cursor.rowcount == 0: raise HTTPException(404, "Task not found")
        db.commit()
        return serialize(db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with closing(connect()) as db:
        cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0: raise HTTPException(404, "Task not found")
        db.commit()


@app.get("/dashboard")
def dashboard():
    today = date.today().isoformat()
    with closing(connect()) as db:
        row = db.execute("SELECT COUNT(*) total, SUM(completed) completed, SUM(CASE WHEN completed=0 AND due_date < ? THEN 1 ELSE 0 END) overdue FROM tasks", (today,)).fetchone()
        courses = db.execute("SELECT course, COUNT(*) tasks, SUM(completed) completed FROM tasks GROUP BY course ORDER BY course").fetchall()
    total = row["total"] or 0
    return {"total_tasks": total, "completed_tasks": row["completed"] or 0, "overdue_tasks": row["overdue"] or 0, "completion_rate": round((row["completed"] or 0) / total * 100, 1) if total else 0, "by_course": [dict(course) for course in courses]}
