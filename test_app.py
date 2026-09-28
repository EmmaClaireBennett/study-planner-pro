import os
from pathlib import Path

os.environ["STUDY_PLANNER_DB"] = str(Path(__file__).with_name("test.db"))
from fastapi.testclient import TestClient
from app import app, init_db

client = TestClient(app)

def setup_module():
    Path(os.environ["STUDY_PLANNER_DB"]).unlink(missing_ok=True)
    init_db()

def test_task_lifecycle_and_dashboard():
    response = client.post("/tasks", json={"title":"Study graphs","course":"Algorithms","due_date":"2026-10-01","priority":"high"})
    assert response.status_code == 201
    task_id = response.json()["id"]
    assert client.get("/tasks?priority=high").json()[0]["title"] == "Study graphs"
    assert client.patch(f"/tasks/{task_id}", json={"completed":True}).json()["completed"] is True
    assert client.get("/dashboard").json()["completed_tasks"] == 1
    assert client.delete(f"/tasks/{task_id}").status_code == 204

def test_missing_task_is_404():
    assert client.patch("/tasks/99999", json={"completed":True}).status_code == 404
