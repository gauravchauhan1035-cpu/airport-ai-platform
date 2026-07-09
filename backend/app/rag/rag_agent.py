"""RAG agent – semantic search over indexed document chunks."""

import logging
import time
from functools import lru_cache

from sqlalchemy.orm import Session

from app.config import get_settings
from app.rag.embedder import embed_query
from app.rag.faiss_store import FAISSStore, get_faiss_store
from app.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class RAGAgent:
    """Performs semantic search over indexed PDF document chunks."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.store = get_faiss_store()
        self.repo = DocumentRepository(db)

    def _search(self, query: str, top_k: int | None = None) -> list[dict]:
        """Search for document chunks most semantically relevant to the query."""
        k = top_k or self.settings.rag_top_k
        logger.info("RAG search: %s (top_k=%d)", query, k)

        if self.store.total_vectors == 0:
            return []

        # Embed the query
        query_vec = embed_query(query)

        # FAISS nearest-neighbour search
        hits = self.store.search(query_vec, top_k=k)
        if not hits:
            return []

        # Fetch chunk records and their parent documents
        chunk_ids = [h["chunk_id"] for h in hits]
        score_map = {h["chunk_id"]: h["score"] for h in hits}

        chunks = self.repo.get_chunks_by_ids(chunk_ids)
        doc_ids = {c.document_id for c in chunks}

        # Build a lookup of document id → Document record
        docs = {}
        for doc_id in doc_ids:
            doc = self.repo.get_by_id(doc_id)
            if doc:
                docs[doc_id] = doc

        results = []
        for chunk in sorted(chunks, key=lambda c: score_map.get(c.id, 0), reverse=True):
            doc = docs.get(chunk.document_id)
            
            # Skip chunks belonging to non-active or deleted documents
            from app.models.document import DocumentStatus
            if not doc or doc.status != DocumentStatus.ACTIVE.value:
                continue
                
            results.append(
                {
                    "document_name": doc.original_name,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "score": round(score_map.get(chunk.id, 0.0), 4),
                }
            )
        return results

    def run(self, question: str) -> dict:
        """
        Perform true RAG: Retrieve relevant chunks and generate a grounded answer using the LLM.
        """
        from app.services.llm_service import LLMService
        from app.prompts.rag_prompt import build_rag_prompt
        import json
        
        start = time.perf_counter()
        
        # 1. Retrieve
        chunks = self._search(question)
        
        answer = ""
        # 2. Synthesize using LLM
        if not chunks:
            answer = "I cannot find any relevant information in the operational documents to answer your question."
        else:
            llm = LLMService()
            system_prompt, user_message = build_rag_prompt(question, chunks)
            
            try:
                response_text = llm.generate(system_prompt, user_message, json_format=True)
                payload = json.loads(response_text)
                answer = payload.get("answer", "Failed to generate a valid answer.")
            except Exception as exc:
                logger.error("RAG synthesis failed: %s", exc)
                answer = "Error generating response from retrieved documents."

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info("RAG synthesis completed in %dms", elapsed_ms)
        
        return {
            "question": question,
            "answer": answer,
            "results": chunks,  # include raw chunks for the Aggregator
            "execution_time_ms": elapsed_ms,
        }

    # Keep legacy search method for backward compatibility with orchestrator until Step 7
    def search(self, question: str) -> dict:
        return self.run(question)
