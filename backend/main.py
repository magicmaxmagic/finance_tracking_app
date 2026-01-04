"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.routers import auth, users, accounts, categories, transactions, budgets, net_worth, dashboard, jobs, data, notifications, fx_rates, analysis, goals, assumptions, scenarios, strategy, onboarding, settings as settings_router, investments, billing, schedule, calendar
from prometheus_fastapi_instrumentator import Instrumentator

# Create app
app = FastAPI(
    title="Finance Tracking API",
    description="Finance analysis and prediction API for mapping optimal paths to a target net worth.",
    version="1.0.0",
)


def _validate_security_settings() -> None:
    if settings.ENVIRONMENT.lower() != "production":
        return
    issues = []
    if not settings.SECRET_KEY or "dev-secret" in settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        issues.append("SECRET_KEY is not set to a strong value")
    if not settings.REFRESH_SECRET_KEY or "dev-refresh" in settings.REFRESH_SECRET_KEY or len(settings.REFRESH_SECRET_KEY) < 32:
        issues.append("REFRESH_SECRET_KEY is not set to a strong value")
    if not settings.COOKIE_SECURE:
        issues.append("COOKIE_SECURE must be enabled in production")
    if not settings.ENCRYPTION_KEY:
        issues.append("ENCRYPTION_KEY must be set for encrypting secrets")
    if issues:
        raise RuntimeError("Security configuration errors: " + "; ".join(issues))


_validate_security_settings()

app.add_middleware(RequestIDMiddleware)
if settings.SECURITY_HEADERS_ENABLED:
    app.add_middleware(
        SecurityHeadersMiddleware,
        csp=settings.CONTENT_SECURITY_POLICY,
        hsts_max_age=settings.HSTS_MAX_AGE,
        include_subdomains=settings.HSTS_INCLUDE_SUBDOMAINS,
        preload=settings.HSTS_PRELOAD,
    )
if settings.ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
if settings.ENFORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(net_worth.router)
app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(data.router)
app.include_router(notifications.router)
app.include_router(fx_rates.router)
app.include_router(analysis.router)
app.include_router(goals.router)
app.include_router(assumptions.router)
app.include_router(scenarios.router)
app.include_router(strategy.router)
app.include_router(onboarding.router)
app.include_router(settings_router.router)
app.include_router(investments.router)
app.include_router(billing.router)
app.include_router(schedule.router)
app.include_router(calendar.router)

if settings.PROMETHEUS_METRICS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
    )
