# Finance Tracking App - Backend

Backend API for personal finance management application.

## Setup

```bash
cd backend

# Create venv
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# DB Migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Structure

- `main.py` - FastAPI entry point
- `app/core/` - Configuration, security, logging
- `app/db/` - Database and sessions
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic schemas
- `app/repositories/` - Data access layer
- `app/services/` - Business logic
- `app/routers/` - API endpoints
- `alembic/` - DB Migrations

## API Documentation

Once the server is running, access: http://localhost:8000/docs

## Tests

```bash
pytest
```

## Environment Variables

See `.env.example` for all available variables.

### Important keys:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret (min 32 characters)
- `DEBUG` - Debug mode (True/False)
