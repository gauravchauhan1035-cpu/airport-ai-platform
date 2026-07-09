"""FAISS index management for document chunk embeddings."""

import json
import logging
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)

_INDEX_FILE = "index.faiss"
_META_FILE = "index_meta.json"


class FAISSStore:
    """Manages a flat L2 FAISS index with chunk-ID metadata."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._index_path = Path(self.settings.faiss_index_path)
        self._index_path.mkdir(parents=True, exist_ok=True)

        self._index: faiss.IndexFlatL2 | None = None
        # Parallel list of chunk DB IDs; position i → chunk_id
        self._chunk_ids: list[int] = []
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load index and metadata from disk if they exist."""
        idx_file = self._index_path / _INDEX_FILE
        meta_file = self._index_path / _META_FILE

        if idx_file.exists() and meta_file.exists():
            self._index = faiss.read_index(str(idx_file))
            with open(meta_file) as f:
                self._chunk_ids = json.load(f)
            logger.info("Loaded FAISS index (%d vectors)", self._index.ntotal)
        else:
            self._index = faiss.IndexFlatL2(self.settings.embedding_dimension)
            self._chunk_ids = []
            logger.info("Created new FAISS index (dim=%d)", self.settings.embedding_dimension)

    def save(self) -> None:
        """Persist index and metadata to disk."""
        if self._index is not None:
            faiss.write_index(self._index, str(self._index_path / _INDEX_FILE))
        with open(self._index_path / _META_FILE, "w") as f:
            json.dump(self._chunk_ids, f)
        logger.info("Saved FAISS index (%d vectors)", len(self._chunk_ids))

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def add(self, embeddings: np.ndarray, chunk_ids: list[int]) -> None:
        """Add embeddings and their corresponding DB chunk IDs to the index."""
        if self._index is None:
            self._index = faiss.IndexFlatL2(self.settings.embedding_dimension)
        self._index.add(embeddings)
        self._chunk_ids.extend(chunk_ids)
        self.save()
        logger.info("Added %d vectors to FAISS index", len(chunk_ids))

    def remove_by_chunk_ids(self, chunk_ids_to_remove: set[int]) -> None:
        """Rebuild the index excluding the specified chunk IDs."""
        if self._index is None or self._index.ntotal == 0:
            return

        # Collect indices to keep
        keep_positions = [
            i for i, cid in enumerate(self._chunk_ids) if cid not in chunk_ids_to_remove
        ]
        if len(keep_positions) == self._index.ntotal:
            return  # Nothing to remove

        # Reconstruct vectors for kept positions
        if keep_positions:
            keep_arr = np.array(keep_positions, dtype=np.int64)
            kept_vecs = self._index.reconstruct_batch(keep_arr)
            kept_ids = [self._chunk_ids[i] for i in keep_positions]
        else:
            kept_vecs = np.empty((0, self.settings.embedding_dimension), dtype=np.float32)
            kept_ids = []

        # Rebuild
        self._index = faiss.IndexFlatL2(self.settings.embedding_dimension)
        if len(kept_vecs) > 0:
            self._index.add(kept_vecs)
        self._chunk_ids = kept_ids
        self.save()
        logger.info("Removed %d vectors; FAISS index now has %d", len(chunk_ids_to_remove), len(self._chunk_ids))

    def search(self, query_vector: np.ndarray, top_k: int | None = None) -> list[dict]:
        """Search for nearest neighbours.

        Returns:
            List of {"chunk_id": int, "score": float} sorted by ascending distance.
        """
        if self._index is None or self._index.ntotal == 0:
            return []
        k = min(top_k or self.settings.rag_top_k, self._index.ntotal)
        q = query_vector.reshape(1, -1).astype(np.float32)
        distances, indices = self._index.search(q, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._chunk_ids):
                continue
            # Convert L2 distance to a similarity score in [0, 1]
            score = float(1 / (1 + dist))
            results.append({"chunk_id": self._chunk_ids[idx], "score": score})
        return results

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal if self._index else 0


@lru_cache(maxsize=1)
def get_faiss_store() -> FAISSStore:
    """Return a cached singleton FAISS store."""
    return FAISSStore()
