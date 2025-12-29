"""Auth-related schemas."""
from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    """Request a password reset token."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8)


class EmailVerificationRequest(BaseModel):
    """Request email verification."""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Confirm email verification."""
    token: str = Field(..., min_length=20)
