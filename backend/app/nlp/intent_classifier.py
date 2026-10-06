"""
Query Intent Classifier
Labels: factual | follow_up | out_of_scope | ambiguous

Uses a TF-IDF + LogisticRegression baseline (fast, no GPU needed).
The model is trained on a small seed dataset at startup if no saved model exists.
Swap to DistilBERT by setting USE_DISTILBERT=true in env (requires GPU).
"""
import os
import pickle
import logging
from pathlib import Path
from typing import Literal

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

IntentLabel = Literal["factual", "follow_up", "out_of_scope", "ambiguous"]

_MODEL_PATH = Path(__file__).parent / "intent_model.pkl"

# ── Seed training data ────────────────────────────────────────────────────────
_SEED_DATA = [
    # factual
    ("What is the capital of France?", "factual"),
    ("How does photosynthesis work?", "factual"),
    ("When was the Eiffel Tower built?", "factual"),
    ("Define machine learning.", "factual"),
    ("What are the symptoms of diabetes?", "factual"),
    ("Who wrote Hamlet?", "factual"),
    ("What is the speed of light?", "factual"),
    ("Explain the water cycle.", "factual"),
    ("What is RAG in NLP?", "factual"),
    ("How does BERT work?", "factual"),
    # follow_up
    ("Can you elaborate on that?", "follow_up"),
    ("What did you mean by the last point?", "follow_up"),
    ("Tell me more about it.", "follow_up"),
    ("And what about the second part?", "follow_up"),
    ("Could you clarify your previous answer?", "follow_up"),
    ("What does that imply?", "follow_up"),
    ("Go on.", "follow_up"),
    ("Explain further.", "follow_up"),
    # out_of_scope
    ("Write me a poem about love.", "out_of_scope"),
    ("What is the best pizza recipe?", "out_of_scope"),
    ("Tell me a joke.", "out_of_scope"),
    ("Book a flight to Paris.", "out_of_scope"),
    ("What movies are playing tonight?", "out_of_scope"),
    ("Play some music.", "out_of_scope"),
    ("What is the weather today?", "out_of_scope"),
    # ambiguous
    ("What about it?", "ambiguous"),
    ("How?", "ambiguous"),
    ("Why?", "ambiguous"),
    ("Is it good?", "ambiguous"),
    ("Does it work?", "ambiguous"),
    ("What do you think?", "ambiguous"),
    ("Can you help?", "ambiguous"),
]


def _build_and_save_model() -> Pipeline:
    texts, labels = zip(*_SEED_DATA)
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        ("clf", LogisticRegression(max_iter=500, C=1.0)),
    ])
    pipe.fit(texts, labels)
    with open(_MODEL_PATH, "wb") as f:
        pickle.dump(pipe, f)
    logger.info("Intent classifier trained and saved to %s", _MODEL_PATH)
    return pipe


def _load_model() -> Pipeline:
    if _MODEL_PATH.exists():
        with open(_MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return _build_and_save_model()


_pipeline: Pipeline | None = None


def get_classifier() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = _load_model()
    return _pipeline


def classify_intent(query: str) -> tuple[IntentLabel, float]:
    """Returns (label, confidence)."""
    clf = get_classifier()
    proba = clf.predict_proba([query])[0]
    idx = int(np.argmax(proba))
    label: IntentLabel = clf.classes_[idx]
    confidence = float(proba[idx])
    logger.info("Intent: %s (%.2f) for query: %.60s", label, confidence, query)
    return label, confidence
