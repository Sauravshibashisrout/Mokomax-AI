"""
Embedding layer — swappable via config.
Supported: all-MiniLM-L6-v2 | BAAI/bge-large-en-v1.5 | openai
"""
import logging
from typing import List
from functools import lru_cache
from app.config import get_settings

logger = logging.getLogger(__name__)

_SENTENCE_TRANSFORMER_MODELS = {
    "all-MiniLM-L6-v2",
    "BAAI/bge-large-en-v1.5",
}


@lru_cache(maxsize=3)
def _get_st_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    logger.info("Loading SentenceTransformer: %s", model_name)
    return SentenceTransformer(model_name)


def embed(texts: List[str], model_name: str | None = None) -> List[List[float]]:
    cfg = get_settings()
    model_name = model_name or cfg.embedding_model

    if model_name in _SENTENCE_TRANSFORMER_MODELS:
        model = _get_st_model(model_name)
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vecs.tolist()

    elif model_name == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=cfg.openai_api_key)
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in resp.data]

    else:
        raise ValueError(f"Unknown embedding model: {model_name}")


def embed_query(text: str, model_name: str | None = None) -> List[float]:
    return embed([text], model_name)[0]
