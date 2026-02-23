# Wellness Tracker API

Production-ready base API for a mental wellness tracking system. Clean architecture, async-first, HIPAA/GDPR-ready foundation.

## Tech Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- Pydantic v2
- Alembic
- JWT authentication
- Docker-ready

## Folder Structure

```
app/
├── main.py                 # FastAPI app entry point
├── core/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── security.py         # JWT, password hashing
│   └── logging.py          # Structured logging
├── api/
│   ├── deps.py             # Dependencies (auth, RBAC, DB)
│   ├── exceptions.py       # Global exception handlers
│   └── routes/
│       ├── auth.py         # POST /auth/register, /login, GET /me
│       ├── client.py       # entries, summary, tasks
│       ├── specialist.py   # clients, client timeline/summary
│       └── health.py       # GET /health
├── domain/
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic request/response schemas
│   └── enums.py            # UserRole, ScaleType, TaskStatus, etc.
├── repositories/
│   ├── user_repository.py
│   ├── specialist_repository.py
│   ├── entry_repository.py
│   ├── task_repository.py
│   └── metric_repository.py
├── services/
│   ├── user_service.py
│   ├── entry_service.py
│   └── analytics_service.py  # Stub
├── llm/
│   ├── extraction_service.py  # Stub
│   └── normalization_service.py  # Stub
└── db/
    ├── base.py             # Declarative base
    └── session.py          # Async session, get_db dependency

migrations/
├── env.py
├── script.py.mako
└── versions/
    └── 001_initial_schema.py

tests/
├── conftest.py
├── test_health.py
├── test_api_root.py
└── test_security.py
```

## Quick Start

```bash
# Copy env
cp .env.example .env
# Edit .env with SECRET_KEY and DATABASE_URL

# Install
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload
```

## Docker

```bash

# API at http://localhost:8000
# Run migrations: docker-compose exec api alembic upgrade head
```

## API Endpoints (MVP)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register/specialist | Register specialist |
| POST | /api/v1/auth/register/client | Register client |
| POST | /api/v1/auth/login | Login |
| GET | /api/v1/auth/me | Current user |
| POST | /api/v1/entries/submit | Submit chrono entry |
| GET | /api/v1/entries/timeline | Get timeline |
| GET | /api/v1/summary | Get summary (stub) |
| POST | /api/v1/tasks | Create task |
| GET | /api/v1/tasks | List tasks |
| GET | /api/v1/specialist/clients | Specialist: list clients |
| GET | /api/v1/specialist/{id}/timeline | Specialist: client timeline |
| GET | /api/v1/specialist/{id}/summary | Specialist: client summary |
| GET | /health | Health check |

## Tests

```bash
pytest tests/ -v
```
