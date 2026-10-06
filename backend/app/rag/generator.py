"""Generate an answer from retrieved chunks using Groq LLaMA3."""
import logging
from typing import List, Dict, Any

from groq import Groq
from app.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are MokoMax AI, a helpful research assistant.
Answer the user's question using ONLY the provided context chunks.
If the answer is not in the context, say "I don't have enough information to answer that."
Always cite the source filename and chunk index at the end of relevant sentences like [source: filename, chunk N].
Be concise and factual."""


def generate_answer(
    query: str,
    chunks: List[Dict[str, Any]],
    history: List[Dict[str, str]] | None = None,
) -> str:
    cfg = get_settings()
    context = "\n\n".join(
        f"[Chunk {i+1} | {c['metadata'].get('filename','?')} | chunk {c['metadata'].get('chunk_index','?')}]\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {query}",
    })

    client = Groq(api_key=cfg.groq_api_key)
    resp = client.chat.completions.create(
        model=cfg.groq_model,
        messages=messages,
        max_tokens=1024,
        temperature=0.2,
    )
    answer = resp.choices[0].message.content.strip()
    logger.info("Generated answer (%d chars) for query: %.60s", len(answer), query)
    return answer
