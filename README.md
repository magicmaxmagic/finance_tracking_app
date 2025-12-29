# Finance Tracking App - SaaS

A finance analysis and prediction platform that models optimal paths to reach a target net worth, built as a multi-user SaaS.

## Quick Start

```bash
# Start all services
make up

# View API documentation
make docs

# Run tests
make test

# View help
make help
```

**Services:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Quick Links

- **CI/CD Setup**: [CI_CD_README.md](CI_CD_README.md) - Configure GitHub Actions pipeline
- **GitHub Secrets**: [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) - SSH and deployment setup

## Features

### Authentication
- Register / Login with JWT (access + refresh tokens)
- HttpOnly cookies with refresh rotation
- Password reset + email verification flows
- Audit logs for auth events
- Secure password hashing with bcrypt
- Authentication middleware

### Expense Management
- Complete CRUD for transactions
- CSV import with automatic deduplication
- Fields: date, amount, currency, description, category, account, tags
- Pagination, filters and text search

### Categories & Rules
- Category CRUD with icon support
- Automatic rules (contains, regex, exact match)
- Smart auto-categorization on import

### Budgets
- Monthly budgets per category
- Calculation: spent, remaining, % consumed
- Alerts and tracking

### Net Worth
- Multiple accounts (cash, savings, credit, debt, investments)
- Monthly snapshots
- Historical evolution curve
- Breakdown by account type

### Dashboard
- KPIs: monthly expenses, burn rate, current net worth
- Charts: expenses by category, monthly evolution, net worth
- Recent transactions

### Account & Settings
- Financial account management
- User settings

---

## Tech Stack

### Backend
- **FastAPI** 0.104.1
- **Python** 3.11+
- **SQLAlchemy 2.0** (async) with PostgreSQL
- **Pydantic v2** (data validation)
- **JWT** (authentication)
- **Alembic** (migrations)

### Frontend
- **Next.js 14+** (App Router)
- **TypeScript**
- **TailwindCSS**
- **SWR** (data fetching)
- **Recharts** (charts)

### Infrastructure
- **Docker** & **Docker Compose**
- **PostgreSQL 15**
- **Redis** (rate limiting + token blacklist)
- **Prometheus** metrics endpoint `/metrics`

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Make (built-in on macOS/Linux, install on Windows)
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Option 1: Using Make (Recommended)

Make provides simple commands for all operations:

```bash
git clone <repo>
cd finance_tracking_app

# See all available commands
make help

# Start everything
make up

# Create test user
make test-user

# View logs
make logs

# Stop services
make down
```

Application will be available at:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Use `make help` for complete command reference.

### Option 2: Using Docker Compose Directly

```bash
git clone <repo>
cd finance_tracking_app

# Configure environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Run with Docker Compose
docker-compose up -d

# Create test user
docker-compose exec backend python scripts/create_test_user.py
```

### Test Credentials

Both methods create a test user:
- **Email**: test@example.com
- **Password**: Check your app logs after running `make test-user`

---

## Project Structure

```
finance_tracking_app/
├── backend/                      # FastAPI API
│   ├── app/
│   │   ├── core/                # Config, security, logger
│   │   ├── db/                  # Database
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── repositories/        # Data access layer
│   │   ├── services/            # Business logic
│   │   └── routers/             # API endpoints
│   ├── alembic/                 # DB migrations
│   ├── scripts/                 # Utilities
│   ├── main.py                  # FastAPI entrypoint
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                    # Next.js App
│   ├── src/
│   │   ├── app/                 # Pages and layouts
│   │   ├── components/          # Reusable components
│   │   ├── hooks/               # Custom hooks (useAuth, useAPI)
│   │   └── lib/                 # Utilities (api, auth, utils)
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml           # Orchestration
└── README.md
```

---

## Architecture

### Backend Layers

1. **Routers**: API endpoints
2. **Services**: Business logic (validation, rules, calculations)
3. **Repositories**: Data access (abstraction)
4. **Models**: SQLAlchemy ORM
5. **Schemas**: Pydantic validation

### Security

- JWT with access + refresh tokens
- Bcrypt password hashing
- Configured CORS
- Pydantic data validation
- User-based authorization

---

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token

### Users
- `GET /api/users/me` - Current profile
- `PUT /api/users/me` - Update profile

### Accounts
- `GET /api/accounts` - All accounts
- `POST /api/accounts` - Create account
- `PUT /api/accounts/{id}` - Update
- `DELETE /api/accounts/{id}` - Delete

### Transactions
- `GET /api/transactions` - Paginated list with filters
- `POST /api/transactions` - Create transaction
- `PUT /api/transactions/{id}` - Update
- `DELETE /api/transactions/{id}` - Delete
- `POST /api/transactions/import/csv` - CSV import

### Categories
- `GET /api/categories` - All categories
- `POST /api/categories` - Create category
- `GET /api/categories/{id}/rules` - Category rules
- `POST /api/categories/{id}/rules` - Create rule

### Budgets
- `GET /api/budgets` - All budgets
- `GET /api/budgets/month/{month}` - Monthly budgets with spending
- `POST /api/budgets` - Create budget

### Net Worth
- `GET /api/net-worth/summary` - Current summary
- `GET /api/net-worth/history` - History

### Dashboard
- `GET /api/dashboard` - Complete dashboard data

---

## Authentication Flow

```
1. Register -> hash password -> create user -> return tokens
2. Login -> verify credentials -> return tokens
3. API calls -> include Authorization: Bearer {token}
4. Token expiration -> use refresh token
5. Refresh -> return new access token
```

---

## Data Model

### Main Schema

```
Users
├── Accounts (cash, savings, credit, debt, etc.)
├── Categories
│   └── CategoryRules (auto-categorization)
├── Transactions
│   ├── Account
│   ├── Category
│   └── Tags
├── Budgets
│   └── Category
└── NetWorthSnapshots
    └── Account
```

### Optimized Indexes

- `transactions(user_id, transaction_date)` - Date queries
- `budgets(user_id, month)` - Monthly queries
- `net_worth_snapshots(user_id, snapshot_date)` - History
- `transactions(import_id)` - CSV deduplication

---

## Testing & Development

### Backend

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Create migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Start dev server
uvicorn main:app --reload

# Tests
pytest
```

### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Start dev server
npm run dev

# Build
npm run build
```

---

## Future Features (v2)

- [ ] Investment portfolio
- [ ] Budget/category sharing
- [ ] Notifications & alerts
- [ ] PDF reports
- [ ] Mobile app
- [ ] Bank integrations
- [ ] Advanced multi-currency
- [ ] Forecasting/predictions

---

## Security

### Implemented Best Practices

- JWT with strong secrets
- Bcrypt password hashing
- Restrictive CORS
- Strict Pydantic validation
- SQL injection protection (SQLAlchemy)
- Rate limiting ready (TODO)
- HTTPS ready (TODO)
- Environment variables for secrets

### To Add in Production

- Rate limiting
- HTTPS/TLS
- CSP headers
- HSTS
- Audit logging
- WAF

---

## Technical Choices

### Why FastAPI?
- Async by default
- Automatic Pydantic validation
- Auto-generated OpenAPI documentation
- Excellent performance
- Modern and actively maintained

### Why Next.js 14 App Router?
- Performant server components
- Simplified routing
- Image optimization
- SEO friendly
- Modern React framework

### Why PostgreSQL?
- Robust and mature
- JSON/Array support
- ACID transactions
- Scalability
- Excellent performance

---

## Troubleshooting

### Database Connection Error
```bash
# Verify postgres is ready
docker-compose exec postgres pg_isready

# Check logs
docker-compose logs postgres
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
# Or stop the service using them
lsof -i :3000  # or 8000
kill -9 <PID>
```

### Frontend Can't Reach Backend
```bash
# Verify NEXT_PUBLIC_API_URL points to backend
# In frontend/.env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Support

For questions or issues, open an issue or contact the team.

---

## License

MIT

---

**Last Updated**: December 2024
**Version**: 1.0.0
