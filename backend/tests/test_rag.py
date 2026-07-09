"""Tests for RAG pipeline components: chunker, repository, and search logic."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.rag.chunker import chunk_pages
from app.repositories.document_repository import DocumentRepository


@pytest.fixture()
def db_session(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test_rag.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ── Chunker ────────────────────────────────────────────────────────────────────

def test_chunk_pages_empty():
    result = chunk_pages([])
    assert result == []


def test_chunk_pages_single_page():
    pages = [{"page_number": 1, "text": "Hello world. " * 50}]
    chunks = chunk_pages(pages)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert "content" in chunk
        assert "page_number" in chunk
        assert chunk["page_number"] == 1
        assert len(chunk["content"]) > 0


def test_chunk_pages_multiple_pages():
    pages = [
        {"page_number": 1, "text": "Page one content. " * 40},
        {"page_number": 2, "text": "Page two content. " * 40},
    ]
    chunks = chunk_pages(pages)
    assert len(chunks) >= 2
    page_numbers = {c["page_number"] for c in chunks}
    assert 1 in page_numbers
    assert 2 in page_numbers


def test_chunk_indices_are_sequential():
    pages = [{"page_number": 1, "text": "Test text. " * 100}]
    chunks = chunk_pages(pages)
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i


def test_chunk_pages_strips_empty_text():
    pages = [{"page_number": 1, "text": "   "}]
    chunks = chunk_pages(pages)
    assert all(c["content"].strip() for c in chunks)


# ── Document Repository ────────────────────────────────────────────────────────

def test_create_document(db_session):
    repo = DocumentRepository(db_session)
    doc = repo.create_document(
        filename="test.pdf",
        original_name="Test Document.pdf",
        page_count=5,
        chunk_count=20,
    )
    assert doc.id is not None
    assert doc.original_name == "Test Document.pdf"
    assert doc.page_count == 5


def test_get_document_by_id(db_session):
    repo = DocumentRepository(db_session)
    doc = repo.create_document("f1.pdf", "File 1.pdf", 3, 12)
    fetched = repo.get_by_id(doc.id)
    assert fetched is not None
    assert fetched.id == doc.id


def test_get_document_not_found(db_session):
    repo = DocumentRepository(db_session)
    result = repo.get_by_id(99999)
    assert result is None


def test_list_all_documents(db_session):
    repo = DocumentRepository(db_session)
    repo.create_document("a.pdf", "A.pdf")
    repo.create_document("b.pdf", "B.pdf")
    docs = repo.list_all()
    assert len(docs) == 2


def test_add_and_get_chunks(db_session):
    repo = DocumentRepository(db_session)
    doc = repo.create_document("chunks.pdf", "Chunked.pdf", 1, 3)
    chunks_data = [
        {"chunk_index": 0, "content": "First chunk.", "page_number": 1},
        {"chunk_index": 1, "content": "Second chunk.", "page_number": 1},
        {"chunk_index": 2, "content": "Third chunk.", "page_number": 1},
    ]
    repo.add_chunks(doc.id, chunks_data)
    fetched_chunks = repo.get_chunks_by_document(doc.id)
    assert len(fetched_chunks) == 3


def test_delete_document_cascades_chunks(db_session):
    from app.models.document_chunk import DocumentChunk

    repo = DocumentRepository(db_session)
    doc = repo.create_document("del.pdf", "ToDelete.pdf", 1, 1)
    chunks_data = [{"chunk_index": 0, "content": "Some text", "page_number": 1}]
    repo.add_chunks(doc.id, chunks_data)

    result = repo.delete_document(doc.id)
    assert result is True

    # Verify cascade deletion
    remaining = db_session.query(DocumentChunk).filter_by(document_id=doc.id).count()
    assert remaining == 0
