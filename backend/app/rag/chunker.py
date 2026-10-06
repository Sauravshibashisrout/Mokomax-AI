"""
Chunking strategies:
  - fixed:     Fixed-size character windows with overlap.
  - recursive: Split on paragraph/sentence/word boundaries, then merge to size.
  - semantic:  Embed sentences, split where cosine similarity drops below threshold.
"""
import re
import logging
from typing import List
from app.config import get_settings

logger = logging.getLogger(__name__)


def chunk_text(text: str, strategy: str | None = None) -> List[str]:
    cfg = get_settings()
    strategy = strategy or cfg.chunking_strategy
    size = cfg.chunk_size
    overlap = cfg.chunk_overlap

    logger.info("Chunking with strategy=%s size=%d overlap=%d", strategy, size, overlap)

    if strategy == "fixed":
        return _fixed_chunks(text, size, overlap)
    elif strategy == "recursive":
        return _recursive_chunks(text, size, overlap)
    elif strategy == "semantic":
        return _semantic_chunks(text, size)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")


# ── Fixed-size ────────────────────────────────────────────────────────────────

def _fixed_chunks(text: str, size: int, overlap: int) -> List[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if c]


# ── Recursive character ───────────────────────────────────────────────────────

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _recursive_chunks(text: str, size: int, overlap: int) -> List[str]:
    return _split_recursive(text, size, overlap, _SEPARATORS)


def _split_recursive(text: str, size: int, overlap: int, seps: List[str]) -> List[str]:
    if len(text) <= size:
        return [text.strip()] if text.strip() else []

    sep = next((s for s in seps if s in text), "")
    parts = text.split(sep) if sep else list(text)

    chunks, current = [], ""
    for part in parts:
        candidate = (current + sep + part) if current else part
        if len(candidate) <= size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            # part itself too big → recurse with next separator
            if len(part) > size:
                next_seps = seps[seps.index(sep) + 1:] if sep in seps else []
                chunks.extend(_split_recursive(part, size, overlap, next_seps or [""]))
                current = ""
            else:
                current = part

    if current:
        chunks.append(current.strip())

    # apply overlap by prepending tail of previous chunk
    if overlap > 0:
        overlapped = [chunks[0]] if chunks else []
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap:]
            overlapped.append((tail + " " + chunks[i]).strip())
        return [c for c in overlapped if c]

    return [c for c in chunks if c]


# ── Semantic ──────────────────────────────────────────────────────────────────

def _semantic_chunks(text: str, max_size: int, threshold: float = 0.75) -> List[str]:
    """Split on sentences; merge until similarity drops or size exceeded."""
    from sentence_transformers import SentenceTransformer
    import numpy as np

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        return []

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences, normalize_embeddings=True)

    chunks, current_sents, current_emb = [], [sentences[0]], embeddings[0]

    for i in range(1, len(sentences)):
        sim = float(np.dot(current_emb, embeddings[i]))
        merged = " ".join(current_sents + [sentences[i]])
        if sim >= threshold and len(merged) <= max_size:
            current_sents.append(sentences[i])
            # update running mean embedding
            current_emb = embeddings[i]
        else:
            chunks.append(" ".join(current_sents))
            current_sents = [sentences[i]]
            current_emb = embeddings[i]

    if current_sents:
        chunks.append(" ".join(current_sents))

    return chunks
