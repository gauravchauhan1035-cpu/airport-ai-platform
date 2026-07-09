"""Sentence-transformer embedding utilities."""

import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Return a cached SentenceTransformer model."""
    settings = get_settings()
    logger.info("Loading embedding model: %s", settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Encode a list of texts into a float32 embedding matrix.

    Args:
        texts: List of strings to embed.

    Returns:
        numpy array of shape (len(texts), embedding_dimension).
    """
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Encode a single query string into a 1-D embedding vector."""
    return embed_texts([query])[0]
