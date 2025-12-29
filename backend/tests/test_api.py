"""Basic tests for the application"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from main import app
from app.db.base import get_db
from app.core.security import hash_password


@pytest.fixture
async def test_db():
    """Create a test database."""
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        from app.models.user import Base
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    yield async_session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register(test_db):
    """Test user registration."""
    async with AsyncClient(base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "test@example.com"
        assert response.cookies.get("access_token") is not None
        assert response.cookies.get("refresh_token") is not None


@pytest.mark.asyncio
async def test_login(test_db):
    """Test user login."""
    async with AsyncClient(base_url="http://test") as client:
        # Register first
        await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123",
            },
        )
        
        # Login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "test@example.com"
        assert response.cookies.get("access_token") is not None


@pytest.mark.asyncio
async def test_get_current_user(test_db):
    """Test getting current user."""
    async with AsyncClient(base_url="http://test") as client:
        # Register and get token
        register_response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpass123",
            },
        )
        # Get current user using cookies
        response = await client.get("/api/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
