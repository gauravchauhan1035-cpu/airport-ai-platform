"""Pydantic schemas for authentication and user responses."""

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Login credentials payload."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Public user representation returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    """Successful login response containing JWT and user info."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Expected JWT payload claims."""

    sub: str  # username
    role: str
    exp: int
    iat: int
