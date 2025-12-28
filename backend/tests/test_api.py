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
        assert "access_token" in data
        assert "refresh_token" in data


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
        assert "access_token" in data


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
        token = register_response.json()["access_token"]
        
        # Get current user
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
