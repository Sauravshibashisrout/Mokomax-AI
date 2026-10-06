"""
Evaluation Harness
Runs a test set through every (chunking_strategy × embedding_model) combination.
Computes:
  - retrieval precision@k  — fraction of top-k chunks that are relevant
  - retrieval recall@k     — fraction of relevant chunks retrieved in top-k
  - answer groundedness    — average groundedness score across test items
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.config import get_settings
from app.rag.chunker import chunk_text
from app.rag.embedder import embed, embed_query
from app.rag.vector_store import upsert_chunks, retrieve
from app.rag.generator import generate_answer
from app.nlp.groundedness import compute_groundedness

logger = logging.getLogger(__name__)

CHUNKING_STRATEGIES = ["fixed", "recursive", "semantic"]
EMBEDDING_MODELS = ["all-MiniLM-L6-v2", "BAAI/bge-large-en-v1.5"]


async def run_evaluation(
    test_items: List[Dict[str, Any]],
    corpus_text: str,
) -> List[Dict[str, Any]]:
    """
    test_items: [{"query": str, "relevant_chunks": [str], "reference_answer": str}]
    corpus_text: full text to chunk and index for the eval run.
    Returns list of result dicts stored in MongoDB.
    """
    cfg = get_settings()
    results = []

    for strategy in CHUNKING_STRATEGIES:
        for emb_model in EMBEDDING_MODELS:
            logger.info("Eval: strategy=%s emb=%s", strategy, emb_model)
            run_id = str(uuid.uuid4())

            # Chunk + embed + index corpus
            chunks = chunk_text(corpus_text, strategy=strategy)
            if not chunks:
                continue
            embeddings = embed(chunks, model_name=emb_model)
            doc_id = f"eval_{run_id}"
            upsert_chunks(
                chunks, embeddings, doc_id,
                filename="eval_corpus",
                chunking_strategy=strategy,
                embedding_model=emb_model,
            )

            precisions, recalls, groundedness_scores = [], [], []

            for item in test_items:
                query = item["query"]
                relevant = set(item.get("relevant_chunks", []))
                q_emb = embed_query(query, model_name=emb_model)
                hits = retrieve(
                    q_emb, top_k=cfg.top_k,
                    embedding_model=emb_model,
                    filters={"doc_id": doc_id},
                )
                retrieved_texts = [h["text"] for h in hits]

                # Precision@k and Recall@k (exact substring match as proxy)
                if relevant:
                    tp = sum(
                        1 for rt in retrieved_texts
                        if any(rel.lower() in rt.lower() or rt.lower() in rel.lower()
                               for rel in relevant)
                    )
                    precisions.append(tp / len(retrieved_texts) if retrieved_texts else 0)
                    recalls.append(tp / len(relevant))

                # Groundedness
                if hits:
                    answer = generate_answer(query, hits)
                    g_score = compute_groundedness(answer, hits)
                    groundedness_scores.append(g_score)

            result = {
                "run_id": run_id,
                "chunking_strategy": strategy,
                "embedding_model": emb_model,
                "precision_at_k": round(sum(precisions) / len(precisions), 4) if precisions else None,
                "recall_at_k": round(sum(recalls) / len(recalls), 4) if recalls else None,
                "avg_groundedness": round(sum(groundedness_scores) / len(groundedness_scores), 4) if groundedness_scores else None,
                "num_test_items": len(test_items),
                "top_k": cfg.top_k,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            results.append(result)
            logger.info("Eval result: %s", result)

    return results
