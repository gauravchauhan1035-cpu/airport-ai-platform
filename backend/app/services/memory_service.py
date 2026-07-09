"""Service for managing conversation memory persistence."""

import logging
from sqlalchemy.orm import Session
from app.models.conversation_message import ConversationMessage

logger = logging.getLogger(__name__)

class MemoryService:
    """Manages conversational history for users."""

    def __init__(self, db: Session, max_history: int = 6):
        self.db = db
        self.max_history = max_history

    def add_message(self, session_id: str | None, role: str, content: str) -> None:
        """Appends a new message to the persistent session history."""
        if not session_id:
            return
            
        msg = ConversationMessage(session_id=session_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()
        logger.debug(f"Saved {role} message to session {session_id}")

    def get_history(self, session_id: str | None) -> list[dict[str, str]]:
        """Retrieves the most recent messages for the given session to inject into LLM context."""
        if not session_id:
            return []
            
        # Get the latest max_history messages, order by created_at DESC, then reverse to chronological
        messages = (
            self.db.query(ConversationMessage)
            .filter(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(self.max_history)
            .all()
        )
        
        # Reverse to chronological order (oldest to newest)
        messages.reverse()
        
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def clear_history(self, session_id: str) -> None:
        """Deletes all messages for a session."""
        self.db.query(ConversationMessage).filter(ConversationMessage.session_id == session_id).delete()
        self.db.commit()
