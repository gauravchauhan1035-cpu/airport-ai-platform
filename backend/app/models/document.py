"""Document model – tracks uploaded PDF files."""

from datetime import datetime

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk


class DocumentStatus(str, Enum):
    """Lifecycle status of a knowledge base document."""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class Document(Base):
    """Uploaded PDF document metadata for the Knowledge Base."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # New fields
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, default="PDF")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=DocumentStatus.ACTIVE.value)
    
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=True)
    
    last_indexed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(  # noqa: F821
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} name={self.original_name} ver={self.version} status={self.status}>"
