import uuid
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.config import get_settings
from app.rag.extractor import extract_text, clean_text
from app.rag.chunker import chunk_text
from app.rag.embedder import embed
from app.rag.vector_store import upsert_chunks

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    chunking_strategy: str = Form(None),
    embedding_model: str = Form(None),
):
    cfg = get_settings()
    strategy = chunking_strategy or cfg.chunking_strategy
    emb_model = embedding_model or cfg.embedding_model

    data = await file.read()
    try:
        raw_text = extract_text(data, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    text = clean_text(raw_text)
    if not text:
        raise HTTPException(status_code=400, detail="No text extracted from document.")

    chunks = chunk_text(text, strategy=strategy)
    embeddings = embed(chunks, model_name=emb_model)

    doc_id = str(uuid.uuid4())
    n = upsert_chunks(
        chunks, embeddings, doc_id,
        filename=file.filename,
        chunking_strategy=strategy,
        embedding_model=emb_model,
    )

    logger.info("Ingested doc_id=%s filename=%s chunks=%d", doc_id, file.filename, n)
    return {"doc_id": doc_id, "filename": file.filename, "num_chunks": n, "strategy": strategy, "embedding_model": emb_model}
