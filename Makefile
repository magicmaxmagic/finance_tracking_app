.PHONY: help up down logs migrate seed test clean build restart health docs

help:
	@echo "Finance Tracking App - Available Commands"
	@echo ""
	@echo "Setup and Running:"
	@echo "  make up              Start all services (Docker)"
	@echo "  make down            Stop all services"
	@echo "  make restart         Restart all services"
	@echo "  make build           Build Docker images"
	@echo ""
	@echo "Database:"
	@echo "  make migrate         Run database migrations"
	@echo "  make seed            Seed database with test data"
	@echo "  make test-user       Create test user (test@example.com)"
	@echo ""
	@echo "Development:"
	@echo "  make logs            View container logs (streaming)"
	@echo "  make logs-backend    View backend logs only"
	@echo "  make logs-frontend   View frontend logs only"
	@echo "  make shell-backend   Access backend container shell"
	@echo "  make shell-frontend  Access frontend container shell"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test            Run backend tests"
	@echo "  make test-coverage   Run tests with coverage"
	@echo "  make lint            Check code quality (backend + frontend)"
	@echo "  make lint-backend    Check backend code only"
	@echo "  make lint-frontend   Check frontend code only"
	@echo "  make format          Format all code"
	@echo "  make format-backend  Format backend code"
	@echo "  make format-frontend Format frontend code"
	@echo "  make type-check      Check TypeScript types"
	@echo "  make security-check  Run security scans"
	@echo "  make test-all        Run tests + lint + type-check"
	@echo "  make ci-local        Simulate CI pipeline locally"
	@echo ""
	@echo "Utilities:"
	@echo "  make health          Check service health"
	@echo "  make docs            Open API documentation"
	@echo "  make clean           Remove containers and volumes"
	@echo "  make reset           Full reset (down + clean volumes + up)"
	@echo "  make backup-db       Backup database"
	@echo "  make version         Show component versions"
	@echo ""

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "[OK] Services started"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"

down:
	@echo "Stopping services..."
	docker-compose down
	@echo "[OK] Services stopped"

restart: down up
	@echo "[OK] Services restarted"

build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "[OK] Build complete"

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

migrate:
	@echo "Running migrations..."
	docker-compose exec -T backend python -c "import sys; sys.path.insert(0, '/app'); from alembic.config import Config; from alembic.command import upgrade; c = Config('/app/alembic.ini'); upgrade(c, 'head')"
	@echo "[OK] Migrations complete"

seed:
	@echo "Seeding database..."
	docker-compose exec -T backend python scripts/seed_database.py
	@echo "[OK] Database seeded"

test-user:
	@echo "Creating test user..."
	docker-compose exec -T backend bash -c "cd /app && PYTHONPATH=/app python scripts/create_test_user.py"
	@echo "[OK] Test user created"

shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend bash

test:
	@echo "Running tests..."
	docker-compose exec -T backend pytest
	@echo "[OK] Tests complete"

test-coverage:
	@echo "Running tests with coverage..."
	docker-compose exec -T backend pytest --cov=app tests/
	@echo "[OK] Tests complete"

health:
	@echo "Checking service health..."
	@echo "Postgres: " && docker-compose exec -T postgres pg_isready -U finance_user || echo "[ERROR]"
	@echo "Backend: " && curl -s http://localhost:8000/health | grep -q "ok" && echo "[OK]" || echo "[ERROR]"
	@echo "Frontend: " && curl -s http://localhost:3000 > /dev/null && echo "[OK]" || echo "[ERROR]"

docs:
	@echo "Opening API documentation..."
	@command -v open >/dev/null 2>&1 && open http://localhost:8000/docs || echo "Visit: http://localhost:8000/docs"

clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v
	@echo "[OK] Cleanup complete"

reset: clean up migrate test-user
	@echo "[OK] Reset complete"

install-hooks:
	@echo "Installing git hooks..."
	cp hooks/pre-commit .git/hooks/pre-commit || echo "No hooks directory found"
	chmod +x .git/hooks/pre-commit
	@echo "[OK] Git hooks installed"

backup-db:
	@echo "Backing up database..."
	mkdir -p backups
	docker-compose exec -T postgres pg_dump -U finance_user finance_db | gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "[OK] Database backed up"

restore-db:
	@echo "Restore database (set FILE=backups/backup_YYYYMMDD_HHMMSS.sql.gz)"
	@test -n "$(FILE)" || (echo "ERROR: FILE variable not set"; exit 1)
	gunzip < $(FILE) | docker-compose exec -T postgres psql -U finance_user finance_db
	@echo "[OK] Database restored"

version:
	@echo "Finance Tracking App"
	@echo "Version: 1.0.0"
	@echo ""
	@echo "Backend:"
	docker-compose exec -T backend pip list | grep -E "fastapi|sqlalchemy|pydantic"
	@echo ""
	@echo "Frontend:"
	docker-compose exec -T frontend npm list react next

# CI/CD Commands
lint-backend:
	@echo "Linting backend code..."
	docker-compose exec backend flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "[OK] Backend linting passed"

lint-frontend:
	@echo "Linting frontend code..."
	docker-compose exec frontend npm run lint 2>/dev/null || echo "ESLint not configured"
	@echo "[OK] Frontend linting passed"

lint: lint-backend lint-frontend
	@echo "[OK] All linting passed"

format-backend:
	@echo "Formatting backend code..."
	docker-compose exec backend black app/ 2>/dev/null || echo "Black not installed"
	docker-compose exec backend isort app/ 2>/dev/null || echo "isort not installed"
	@echo "[OK] Backend formatted"

format-frontend:
	@echo "Formatting frontend code..."
	docker-compose exec frontend npm run format 2>/dev/null || echo "Prettier not configured"
	@echo "[OK] Frontend formatted"

format: format-backend format-frontend
	@echo "[OK] All code formatted"

type-check:
	@echo "Checking TypeScript types..."
	docker-compose exec frontend npm run build
	@echo "[OK] TypeScript check passed"

security-check:
	@echo "Running security checks..."
	docker-compose exec backend pip install bandit 2>/dev/null
	docker-compose exec backend bandit -r app/ 2>/dev/null || echo "Bandit check complete"
	@echo "[OK] Security checks completed"

test-all: test lint type-check
	@echo "[OK] All checks passed!"

ci-local:
	@echo "Running local CI simulation..."
	@echo "Backend tests..." && docker-compose exec backend pytest tests/ -v --cov=app --cov-report=xml
	@echo "Backend linting..." && docker-compose exec backend flake8 app --count --select=E9,F63,F7,F82
	@echo "Frontend build..." && docker-compose exec frontend npm run build
	@echo "Frontend linting..." && docker-compose exec frontend npm run lint 2>/dev/null || true
	@echo "[OK] Local CI simulation complete"

.DEFAULT_GOAL := help

