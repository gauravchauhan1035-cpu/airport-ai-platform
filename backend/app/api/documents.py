"""Documents API – upload, list, delete PDFs and perform semantic search."""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.rag.chunker import chunk_pages
from app.rag.embedder import embed_texts
from app.rag.faiss_store import get_faiss_store
from app.rag.pdf_extractor import extract_text_by_page, get_page_count
from app.rag.rag_agent import RAGAgent
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

_PDF_STORAGE = None  # Resolved lazily from settings


def _get_storage_path() -> Path:
    from app.config import get_settings
    path = Path(get_settings().pdf_storage_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> DocumentResponse:
    """Upload a new PDF document. Role: admin only."""
    return await _process_upload(file, db, current_user.username)


@router.put("/{document_id}/replace", response_model=DocumentResponse)
async def replace_document(
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> DocumentResponse:
    """Replace an existing document with a new version."""
    repo = DocumentRepository(db)
    old_doc = repo.get_by_id(document_id)
    if not old_doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Archive the old document and remove its vectors
    _remove_from_faiss(repo, old_doc.id)
    repo.update_status(old_doc.id, "ARCHIVED")
    
    # Process new upload with bumped version
    return await _process_upload(file, db, current_user.username, original_name=old_doc.original_name, version=old_doc.version + 1)


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> DocumentResponse:
    """Re-index a document: delete existing vectors, re-chunk, and re-embed."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # 1. Remove old vectors
    _remove_from_faiss(repo, doc.id)
    
    # 2. Delete old chunks from DB (via direct query to avoid cascading the whole doc)
    db.query(repo.db.get_class("DocumentChunk")).filter_by(document_id=doc.id).delete()
    db.commit()
    
    # 3. Re-process PDF
    pdf_path = _get_storage_path() / doc.filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file missing from storage")
        
    try:
        pages = extract_text_by_page(pdf_path)
        chunks = chunk_pages(pages)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Failed to re-parse PDF.") from exc
        
    # 4. Save new chunks and embed
    if chunks:
        db_chunks = repo.add_chunks(doc.id, chunks)
        texts = [c["content"] for c in chunks]
        embeddings = embed_texts(texts)
        chunk_db_ids = [c.id for c in db_chunks]
        store = get_faiss_store()
        store.add(embeddings, chunk_db_ids)
        
    repo.update_chunk_count(doc.id, len(chunks))
    db.refresh(doc)
    logger.info("Re-indexed document id=%d with %d new chunks", doc.id, len(chunks))
    return DocumentResponse.model_validate(doc)


@router.post("/{document_id}/archive", response_model=DocumentResponse)
def archive_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> DocumentResponse:
    """Archive a document, removing it from FAISS but keeping metadata/storage."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    _remove_from_faiss(repo, doc.id)
    repo.update_status(doc.id, "ARCHIVED")
    db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> DocumentListResponse:
    """Return all uploaded documents."""
    repo = DocumentRepository(db)
    docs = repo.list_all()
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> None:
    """Hard delete a document: remove DB record, FAISS vectors, and PDF file."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    _remove_from_faiss(repo, document_id)
    
    pdf_path = _get_storage_path() / doc.filename
    pdf_path.unlink(missing_ok=True)
    
    repo.delete_document(document_id)
    logger.info("Hard deleted document id=%d", document_id)


@router.post("/search", response_model=SearchResponse)
def search_documents(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SearchResponse:
    """Perform semantic search over indexed document chunks."""
    agent = RAGAgent(db)
    import time
    start = time.perf_counter()
    chunks = agent._search(query=payload.query, top_k=payload.top_k)
    elapsed = int((time.perf_counter() - start) * 1000)
    return SearchResponse(
        query=payload.query,
        results=chunks,
        execution_time_ms=elapsed,
    )


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _remove_from_faiss(repo: DocumentRepository, document_id: int) -> None:
    chunks = repo.get_chunks_by_document(document_id)
    if chunks:
        chunk_ids_to_remove = {c.id for c in chunks}
        store = get_faiss_store()
        store.remove_by_chunk_ids(chunk_ids_to_remove)


async def _process_upload(
    file: UploadFile, 
    db: Session, 
    username: str, 
    original_name: str | None = None,
    version: int = 1
) -> DocumentResponse:
    # Validate content type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    # Sanitize filename
    raw_name = file.filename or "upload.pdf"
    # Strip path traversal characters
    safe_name = raw_name.replace("..", "").replace("/", "").replace("\\", "")
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    storage = _get_storage_path()
    unique_filename = f"{uuid.uuid4().hex}.pdf"
    pdf_path = storage / unique_filename

    content = await file.read()

    # File size limit: 10MB
    max_size_bytes = 10 * 1024 * 1024  # 10MB
    if len(content) > max_size_bytes:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit.")

    if len(content) == 0:
        raise HTTPException(status_code=422, detail="Empty file uploaded.")

    # Validate PDF magic bytes (%PDF-)
    if not content[:5] == b"%PDF-":
        raise HTTPException(status_code=422, detail="Invalid PDF file. File header does not match PDF format.")

    pdf_path.write_bytes(content)
    logger.info("Saved PDF: %s (%d bytes, uploaded by %s)", unique_filename, len(content), username)

    try:
        page_count = get_page_count(pdf_path)
        pages = extract_text_by_page(pdf_path)
        chunks = chunk_pages(pages)
    except Exception as exc:
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Failed to process PDF.") from exc

    repo = DocumentRepository(db)
    doc = repo.create_document(
        filename=unique_filename,
        original_name=original_name or safe_name,
        document_type="PDF",
        version=version,
        page_count=page_count,
        chunk_count=len(chunks),
        embedding_model="all-MiniLM-L6-v2",
        file_path=str(pdf_path),
        created_by=username,
    )

    if chunks:
        db_chunks = repo.add_chunks(doc.id, chunks)
        texts = [c["content"] for c in chunks]
        embeddings = embed_texts(texts)
        chunk_db_ids = [c.id for c in db_chunks]
        store = get_faiss_store()
        store.add(embeddings, chunk_db_ids)

    return DocumentResponse.model_validate(doc)
