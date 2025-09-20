"""User models for authentication and profile management."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserSignupRequest(BaseModel):
    """Request model for user signup."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long")
    display_name: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response model for user data."""
    uid: str
    email: str
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    """Response model for authentication."""
    success: bool
    message: str
    user: Optional[UserResponse] = None
    token: Optional[str] = None


class ErrorResponse(BaseModel):
    """Response model for errors."""
    success: bool = False
    message: str
    error_code: Optional[str] = None


class TokenData(BaseModel):
    """Token data model."""
    uid: str
    email: str
    email_verified: bool
