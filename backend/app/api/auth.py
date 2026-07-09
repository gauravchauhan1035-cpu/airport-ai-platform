"""Authentication endpoints: login, logout, and current-user retrieval."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.utils.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate with username + password, return a signed JWT.

    Raises:
        401 if credentials are invalid or account is disabled.
    """
    repo = UserRepository(db)
    user = repo.get_by_username(payload.username)

    if user is None or not verify_password(payload.password, user.hashed_password):
        logger.warning("Failed login attempt for username: %s", payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact an administrator.",
        )

    token = create_access_token({"sub": user.username, "role": user.role})
    logger.info("User logged in: %s (role=%s)", user.username, user.role)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: User = Depends(get_current_user)) -> None:
    """Stateless logout – instructs the client to discard its token.

    JWT invalidation is client-side; server just confirms the token was valid.
    """
    logger.info("User logged out: %s", current_user.username)


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
