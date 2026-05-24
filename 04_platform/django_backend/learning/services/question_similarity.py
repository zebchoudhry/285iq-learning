"""
Semantic similarity helpers for Question deduplication and near-duplicate detection.

Requires HF_EMBEDDINGS_ENABLED=True and sentence-transformers installed.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List, Sequence, Tuple

from django.conf import settings


class EmbeddingsNotAvailable(Exception):
    """Raised when embedding support is disabled or dependencies are missing."""


def embeddings_available() -> bool:
    if not getattr(settings, "HF_EMBEDDINGS_ENABLED", False):
        return False
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def require_embeddings():
    if not getattr(settings, "HF_EMBEDDINGS_ENABLED", False):
        raise EmbeddingsNotAvailable(
            "Set HF_EMBEDDINGS_ENABLED=true in .env to use semantic similarity."
        )
    try:
        import sentence_transformers  # noqa: F401
    except ImportError as exc:
        raise EmbeddingsNotAvailable(
            "Install sentence-transformers: pip install sentence-transformers"
        ) from exc


@lru_cache(maxsize=1)
def _load_model():
    require_embeddings()
    from sentence_transformers import SentenceTransformer

    model_id = getattr(
        settings,
        "HF_EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    return SentenceTransformer(model_id)


def embed_texts(texts: Sequence[str]) -> List[List[float]]:
    """Return L2-normalized embedding vectors for each text."""
    if not texts:
        return []
    model = _load_model()
    vectors = model.encode(
        list(texts),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [vec.tolist() for vec in vectors]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Dot product of normalized vectors (cosine similarity)."""
    return float(sum(x * y for x, y in zip(a, b)))


def find_near_duplicate_pairs(
    items: Iterable[Tuple[int, str]],
    threshold: float = 0.92,
) -> List[Tuple[int, int, float]]:
    """
    Find pairs of (id, text) with cosine similarity >= threshold.

    Uses a simple O(n^2) scan — suitable for topic-level batches (< few thousand).
    """
    rows = [(qid, (text or "").strip()) for qid, text in items if (text or "").strip()]
    if len(rows) < 2:
        return []

    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    vectors = embed_texts(texts)

    pairs: List[Tuple[int, int, float]] = []
    n = len(rows)
    for i in range(n):
        for j in range(i + 1, n):
            score = cosine_similarity(vectors[i], vectors[j])
            if score >= threshold:
                pairs.append((ids[i], ids[j], round(score, 4)))
    pairs.sort(key=lambda p: -p[2])
    return pairs
