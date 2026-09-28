# Study Planner Pro

A complete study-planning REST API for students. It uses FastAPI and SQLite to manage courses and tasks, calculate overdue work, and expose dashboard analytics.

## Features

- SQLite persistence with automatic database initialization
- CRUD operations for study tasks
- Course, priority, completion, and due-date filters
- Dashboard summary with completion rate and overdue count
- Pydantic validation and useful HTTP errors
- Automated tests for the core API workflow

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open <http://127.0.0.1:8000/docs> for interactive API documentation.

## Test

```bash
pytest
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Review algorithms","course":"CS 201","due_date":"2026-10-01","priority":"high"}'
```

## Next extensions

Add authentication, recurring tasks, calendar export, and a frontend client.
