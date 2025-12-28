"""User service for user-related business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.user import UserCreate, UserResponse


class UserService:
    """Service for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
        self.session = session
    
    async def register(self, user_data: UserCreate) -> dict:
        """Register a new user."""
        # Check if user exists
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User already exists")
        
        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        user = await self.repository.create(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "user": UserResponse.from_orm(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    
    async def login(self, email: str, password: str) -> dict:
        """Login user."""
        user = await self.repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")
        
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("User is inactive")
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "user": UserResponse.from_orm(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    
    async def get_user(self, user_id: int) -> UserResponse:
        """Get user by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return UserResponse.from_orm(user)
    
    async def update_user(self, user_id: int, **kwargs) -> UserResponse:
        """Update user."""
        # Hash password if provided
        if "password" in kwargs and kwargs["password"]:
            kwargs["hashed_password"] = hash_password(kwargs.pop("password"))
        
        user = await self.repository.update(user_id, **kwargs)
        if not user:
            raise ValueError("User not found")
        
        return UserResponse.from_orm(user)
