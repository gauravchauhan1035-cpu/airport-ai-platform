"""Text chunking using LangChain's RecursiveCharacterTextSplitter."""

import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings

logger = logging.getLogger(__name__)


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Split page-level text into overlapping chunks.

    Args:
        pages: List of {"page_number": int, "text": str} dicts from pdf_extractor.

    Returns:
        List of {"chunk_index": int, "content": str, "page_number": int} dicts.
    """
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        length_function=len,
        add_start_index=False,
    )

    chunks = []
    chunk_index = 0
    for page in pages:
        page_chunks = splitter.split_text(page["text"])
        for chunk_text in page_chunks:
            chunk_text = chunk_text.strip()
            if chunk_text:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk_text,
                        "page_number": page["page_number"],
                    }
                )
                chunk_index += 1

    logger.info("Created %d chunks from %d pages", len(chunks), len(pages))
    return chunks
