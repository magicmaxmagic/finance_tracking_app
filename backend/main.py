"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import RequestIDMiddleware
from app.routers import auth, users, accounts, categories, transactions, budgets, net_worth, dashboard, jobs, data, notifications, fx_rates
from prometheus_fastapi_instrumentator import Instrumentator

# Create app
app = FastAPI(
    title="Finance Tracking API",
    description="Finance analysis and prediction API for mapping optimal paths to a target net worth.",
    version="1.0.0",
)

app.add_middleware(RequestIDMiddleware)

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
