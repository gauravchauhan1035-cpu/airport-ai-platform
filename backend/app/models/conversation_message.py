"""SQLAlchemy model for conversation messages."""

import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database.base import Base

class ConversationMessage(Base):
    """Stores conversation history for a given session."""
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
