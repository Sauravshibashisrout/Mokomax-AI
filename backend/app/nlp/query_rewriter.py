"""
Query Rewriter
Rewrites ambiguous or follow-up queries by injecting recent conversation history
into a Groq LLaMA3 prompt so retrieval gets a self-contained query.
"""
import logging
from typing import List, Dict

from groq import Groq
from app.config import get_settings

logger = logging.getLogger(__name__)

_REWRITE_PROMPT = """You are a query rewriting assistant.
Given the conversation history and a follow-up or ambiguous question, rewrite the question
as a single, self-contained, specific query suitable for document retrieval.
Output ONLY the rewritten query — no explanation.

Conversation history:
{history}

Original question: {query}
Rewritten query:"""


def rewrite_query(query: str, history: List[Dict[str, str]]) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": "..."}
    Returns rewritten query string.
    """
    cfg = get_settings()
    if not history:
        return query

    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in history[-6:]
    )
    prompt = _REWRITE_PROMPT.format(history=history_text, query=query)

    client = Groq(api_key=cfg.groq_api_key)
    resp = client.chat.completions.create(
        model=cfg.groq_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=128,
        temperature=0.0,
    )
    rewritten = resp.choices[0].message.content.strip()
    logger.info("Rewritten query: %s → %s", query[:60], rewritten[:60])
    return rewritten
