"""
Groundedness / Hallucination Detector

Two-stage check:
1. Embedding cosine similarity between answer and each retrieved chunk → max score.
2. (Optional) NLI entailment using a cross-encoder for higher accuracy.

Returns a groundedness score in [0, 1].
Score < threshold → flagged as low-confidence.
"""
import logging
from typing import List, Dict, Any

import numpy as np
from app.config import get_settings

logger = logging.getLogger(__name__)


def _cosine(a: List[float], b: List[float]) -> float:
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def compute_groundedness(
    answer: str,
    chunks: List[Dict[str, Any]],
    use_nli: bool = False,
) -> float:
    """
    Returns groundedness score in [0, 1].
    chunks: list of {"text": ..., "metadata": ..., "score": ...}
    """
    if not chunks:
        return 0.0

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    chunk_texts = [c["text"] for c in chunks]
    all_texts = [answer] + chunk_texts
    embeddings = model.encode(all_texts, normalize_embeddings=True)

    answer_emb = embeddings[0]
    chunk_embs = embeddings[1:]

    sims = [_cosine(answer_emb.tolist(), ce.tolist()) for ce in chunk_embs]
    embedding_score = float(max(sims))

    if not use_nli:
        logger.info("Groundedness (embedding): %.3f", embedding_score)
        return embedding_score

    # NLI stage — uses cross-encoder/nli-deberta-v3-small
    try:
        from transformers import pipeline as hf_pipeline
        nli = hf_pipeline("text-classification", model="cross-encoder/nli-deberta-v3-small")
        best_chunk = chunk_texts[int(np.argmax(sims))]
        result = nli(f"{best_chunk} [SEP] {answer}", truncation=True, max_length=512)[0]
        entailment_score = result["score"] if result["label"] == "ENTAILMENT" else 1 - result["score"]
        combined = 0.5 * embedding_score + 0.5 * entailment_score
        logger.info(
            "Groundedness embedding=%.3f nli=%.3f combined=%.3f",
            embedding_score, entailment_score, combined,
        )
        return combined
    except Exception as e:
        logger.warning("NLI check failed (%s), using embedding score only", e)
        return embedding_score


def is_flagged(score: float) -> bool:
    return score < get_settings().groundedness_threshold
