"""User data access layer."""

import logging

from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        """Return the user with the given username, or None."""
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_id(self, user_id: int) -> User | None:
        """Return the user with the given id, or None."""
        return self.db.query(User).filter(User.id == user_id).first()

    def update_password(self, user: User, new_hashed_password: str) -> User:
        """Update the user's hashed password in-place and commit."""
        user.hashed_password = new_hashed_password
        self.db.commit()
        self.db.refresh(user)
        logger.info("Password updated for user: %s", user.username)
        return user

    def list_all(self) -> list[User]:
        """Return all users ordered by id."""
        return self.db.query(User).order_by(User.id).all()
