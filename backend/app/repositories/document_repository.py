"""CRUD repository for documents and their chunks."""

import logging

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for document and chunk CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Documents ─────────────────────────────────────────────────────────────

    def create_document(
        self,
        filename: str,
        original_name: str,
        document_type: str = "PDF",
        version: int = 1,
        page_count: int = 0,
        chunk_count: int = 0,
        embedding_model: str | None = None,
        file_path: str | None = None,
        created_by: str | None = None,
    ) -> Document:
        """Create and persist a new Document record."""
        from app.models.document import DocumentStatus
        from datetime import datetime, timezone
        
        doc = Document(
            filename=filename,
            original_name=original_name,
            document_type=document_type,
            version=version,
            status=DocumentStatus.ACTIVE.value,
            page_count=page_count,
            chunk_count=chunk_count,
            embedding_model=embedding_model,
            file_path=file_path,
            created_by=created_by,
            last_indexed=datetime.now(timezone.utc),
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        logger.info("Created document record: id=%d name=%s version=%d", doc.id, doc.original_name, doc.version)
        return doc

    def get_by_id(self, document_id: int) -> Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_by_filename(self, filename: str) -> Document | None:
        return self.db.query(Document).filter(Document.filename == filename).first()
        
    def get_active_by_original_name(self, original_name: str) -> Document | None:
        """Find the currently active version of a document by its logical name."""
        from app.models.document import DocumentStatus
        return self.db.query(Document).filter(
            Document.original_name == original_name,
            Document.status == DocumentStatus.ACTIVE.value
        ).first()

    def list_all(self) -> list[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()

    def update_status(self, document_id: int, status: str) -> bool:
        """Update the document status (e.g., ARCHIVED, DELETED)."""
        doc = self.get_by_id(document_id)
        if doc is None:
            return False
        doc.status = status
        self.db.commit()
        logger.info("Updated document status: id=%d status=%s", document_id, status)
        return True

    def delete_document(self, document_id: int) -> bool:
        """Delete document and all its chunks (cascade). Returns True if found."""
        doc = self.get_by_id(document_id)
        if doc is None:
            return False
        self.db.delete(doc)
        self.db.commit()
        logger.info("Deleted document: id=%d", document_id)
        return True

    def update_chunk_count(self, document_id: int, chunk_count: int) -> None:
        """Update the stored chunk count for a document."""
        from datetime import datetime, timezone
        doc = self.get_by_id(document_id)
        if doc:
            doc.chunk_count = chunk_count
            doc.last_indexed = datetime.now(timezone.utc)
            self.db.commit()

    # ── Chunks ────────────────────────────────────────────────────────────────

    def add_chunks(self, document_id: int, chunks: list[dict]) -> list[DocumentChunk]:
        """Bulk-insert chunks for a document.

        Args:
            document_id: Parent document ID.
            chunks: List of dicts with keys: chunk_index, content, page_number.
        """
        records = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                page_number=c.get("page_number", 1),
            )
            for c in chunks
        ]
        self.db.add_all(records)
        self.db.commit()
        for r in records:
            self.db.refresh(r)
        logger.info("Inserted %d chunks for document_id=%d", len(records), document_id)
        return records

    def get_chunks_by_document(self, document_id: int) -> list[DocumentChunk]:
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

    def get_chunks_by_ids(self, chunk_ids: list[int]) -> list[DocumentChunk]:
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.id.in_(chunk_ids))
            .all()
        )
