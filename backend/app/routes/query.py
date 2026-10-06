import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.config import get_settings
from app.nlp.intent_classifier import classify_intent
from app.nlp.query_rewriter import rewrite_query
from app.rag.embedder import embed_query
from app.rag.vector_store import retrieve
from app.rag.generator import generate_answer
from app.nlp.groundedness import compute_groundedness, is_flagged

router = APIRouter()
logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = (
    "I'm MokoMax AI, a document-grounded assistant. "
    "I can only answer questions based on uploaded documents. "
    "Your query appears to be outside my scope — please upload relevant documents and try again."
)


class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"
    history: List[Dict[str, str]] = []
    embedding_model: str | None = None
    doc_id: str | None = None


@router.post("/query")
async def query_endpoint(req: QueryRequest):
    cfg = get_settings()
    emb_model = req.embedding_model or cfg.embedding_model
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Intent classification
    intent, intent_conf = classify_intent(req.query)

    if intent == "out_of_scope":
        response = {
            "answer": FALLBACK_RESPONSE,
            "intent": intent,
            "intent_confidence": intent_conf,
            "groundedness_score": None,
            "flagged": False,
            "sources": [],
            "rewritten_query": None,
            "timestamp": ts,
        }
        await _log_chat(req.session_id, req.query, FALLBACK_RESPONSE, response, ts)
        return response

    # 2. Query rewrite for ambiguous/follow-up
    rewritten = req.query
    if intent in ("ambiguous", "follow_up") and req.history:
        rewritten = rewrite_query(req.query, req.history)

    # 3. Embed + retrieve
    q_emb = embed_query(rewritten, model_name=emb_model)
    filters = {"doc_id": req.doc_id} if req.doc_id else None
    chunks = retrieve(q_emb, top_k=cfg.top_k, embedding_model=emb_model, filters=filters)

    if not chunks:
        answer = "No relevant documents found. Please upload documents first."
        response = {
            "answer": answer,
            "intent": intent,
            "intent_confidence": intent_conf,
            "groundedness_score": None,
            "flagged": False,
            "sources": [],
            "rewritten_query": rewritten if rewritten != req.query else None,
            "timestamp": ts,
        }
        await _log_chat(req.session_id, req.query, answer, response, ts)
        return response

    # 4. Generate
    answer = generate_answer(rewritten, chunks, history=req.history)

    # 5. Groundedness check
    g_score = compute_groundedness(answer, chunks)
    flagged = is_flagged(g_score)

    sources = [
        {
            "filename": c["metadata"].get("filename"),
            "chunk_index": c["metadata"].get("chunk_index"),
            "score": round(c["score"], 3),
            "text_preview": c["text"][:200],
        }
        for c in chunks
    ]

    response = {
        "answer": answer,
        "intent": intent,
        "intent_confidence": round(intent_conf, 3),
        "groundedness_score": round(g_score, 3),
        "flagged": flagged,
        "sources": sources,
        "rewritten_query": rewritten if rewritten != req.query else None,
        "timestamp": ts,
    }

    await _log_chat(req.session_id, req.query, answer, response, ts)

    if flagged:
        logger.warning("Flagged low-groundedness response: score=%.3f query=%.60s", g_score, req.query)

    return response


async def _log_chat(session_id, query, answer, full_response, ts):
    pass
