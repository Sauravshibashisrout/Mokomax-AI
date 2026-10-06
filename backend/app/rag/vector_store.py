"""ChromaDB vector store — upsert chunks and retrieve top-k."""
import logging
import uuid
from typing import List, Dict, Any
import chromadb
from app.config import get_settings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        cfg = get_settings()
        _client = chromadb.PersistentClient(path=cfg.chroma_persist_dir)
    return _client


def _collection_name(embedding_model: str) -> str:
    """Separate collection per embedding model to avoid dimension mismatch."""
    return "mokomax_" + embedding_model.replace("/", "_").replace("-", "_")


def upsert_chunks(
    chunks: List[str],
    embeddings: List[List[float]],
    doc_id: str,
    filename: str,
    chunking_strategy: str,
    embedding_model: str,
) -> int:
    client = _get_client()
    col = client.get_or_create_collection(
        name=_collection_name(embedding_model),
        metadata={"hnsw:space": "cosine"},
    )
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "chunk_index": i,
            "chunking_strategy": chunking_strategy,
            "embedding_model": embedding_model,
        }
        for i in range(len(chunks))
    ]
    col.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    logger.info("Upserted %d chunks for doc_id=%s", len(chunks), doc_id)
    return len(chunks)


def retrieve(
    query_embedding: List[float],
    top_k: int,
    embedding_model: str,
    filters: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    client = _get_client()
    col_name = _collection_name(embedding_model)
    try:
        col = client.get_collection(col_name)
    except Exception:
        logger.warning("Collection %s not found", col_name)
        return []

    where = filters or None
    results = col.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({"text": doc, "metadata": meta, "score": 1 - dist})
    return hits
