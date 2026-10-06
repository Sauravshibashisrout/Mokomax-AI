# MokoMax AI — Full-Stack RAG Chatbot

An academic-grade Retrieval-Augmented Generation (RAG) chatbot with real NLP components for comparative study.

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # fill in your keys
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

---

## Architecture Overview

```
User Query
    │
    ▼
Intent Classifier ──► out_of_scope ──► Fallback Response
    │
    ▼ (factual / follow_up / ambiguous)
Query Rewriter (if follow_up or ambiguous + history)
    │
    ▼
Embedding Layer (MiniLM / BGE-large / OpenAI)
    │
    ▼
ChromaDB Vector Store ──► Top-K Retrieval
    │
    ▼
Groq LLaMA3 Generation (grounded prompt)
    │
    ▼
Groundedness Detector ──► Score + Flag
    │
    ▼
Response + Sources + Badge → Frontend
```

---

## NLP Methodology

### 1. Chunking Strategies

Chunking is the process of splitting a document into smaller segments before indexing. The choice of strategy directly affects retrieval quality.

**Fixed-size chunking** (`strategy=fixed`)
- Splits text into windows of `CHUNK_SIZE` characters with `CHUNK_OVERLAP` overlap.
- Simple and fast. Works well for uniform documents.
- Risk: may split mid-sentence, losing semantic coherence.

**Recursive character chunking** (`strategy=recursive`)
- Tries to split on paragraph breaks (`\n\n`), then newlines, then sentences, then words — recursively until chunks fit within `CHUNK_SIZE`.
- Preserves natural text boundaries better than fixed-size.
- Overlap is applied post-split to maintain context continuity.

**Semantic chunking** (`strategy=semantic`)
- Embeds each sentence using `all-MiniLM-L6-v2`, then merges adjacent sentences while their cosine similarity stays above a threshold (default 0.75).
- Produces semantically coherent chunks regardless of character count.
- Most expensive (requires embedding at ingest time) but best for heterogeneous documents.

**Why it matters for retrieval:** Smaller, coherent chunks improve precision (retrieved chunks are more focused). Larger chunks improve recall (less risk of splitting relevant content). The evaluation harness measures this trade-off empirically.

---

### 2. Embedding Models

Embeddings convert text into dense vectors for similarity search. Three models are supported:

| Model | Dimensions | Notes |
|---|---|---|
| `all-MiniLM-L6-v2` | 384 | Fast, lightweight, good general purpose |
| `BAAI/bge-large-en-v1.5` | 1024 | Higher quality, slower, better for technical text |
| `openai/text-embedding-3-small` | 1536 | API-based, strong performance, costs per token |

Each embedding model gets its own ChromaDB collection to avoid dimension mismatch. The config key `EMBEDDING_MODEL` controls which is active at runtime.

---

### 3. Query Intent Classification

Before retrieval, every query is classified into one of four intents:

- **factual** — a direct question answerable from documents (e.g., "What is RAG?")
- **follow_up** — refers to a previous answer (e.g., "Can you elaborate?")
- **out_of_scope** — unrelated to the document domain (e.g., "Tell me a joke")
- **ambiguous** — too vague to retrieve without context (e.g., "How?")

**Implementation:** A TF-IDF + Logistic Regression pipeline trained on a seed dataset of ~30 labelled examples. This is intentionally lightweight — it runs in <1ms with no GPU. The model is saved to `intent_model.pkl` on first run.

**Routing logic:**
- `out_of_scope` → return a fallback message, skip LLM entirely (saves cost + avoids hallucination)
- `follow_up` or `ambiguous` + history → rewrite query before retrieval
- `factual` → proceed directly to retrieval

**Upgrade path:** Replace the sklearn pipeline with a fine-tuned DistilBERT by loading `distilbert-base-uncased` via HuggingFace `transformers` and fine-tuning on a larger labelled dataset.

---

### 4. Query Rewriting

When a query is classified as `follow_up` or `ambiguous`, the last 6 turns of conversation history are injected into a Groq LLaMA3 prompt that rewrites the query into a self-contained form.

Example:
- History: "User: What is BERT? Assistant: BERT is a transformer model..."
- Query: "How was it trained?"
- Rewritten: "How was the BERT transformer model trained?"

This ensures the retrieval step gets a specific, context-rich query rather than a pronoun-heavy fragment.

---

### 5. Hallucination / Groundedness Detection

After generation, the answer is compared against the retrieved chunks to estimate how well it is grounded in the source material.

**Method:**
1. Embed the answer and all retrieved chunks using `all-MiniLM-L6-v2`.
2. Compute cosine similarity between the answer embedding and each chunk embedding.
3. Take the maximum similarity as the groundedness score (0–1).
4. Optionally run an NLI (Natural Language Inference) cross-encoder (`cross-encoder/nli-deberta-v3-small`) to check entailment between the best chunk and the answer. The final score is the average of embedding similarity and NLI entailment probability.

**Flagging:** Answers with score < `GROUNDEDNESS_THRESHOLD` (default 0.4) are:
- Marked with a "⚠ Low Confidence" badge in the UI
- Logged to the `flagged_responses` MongoDB collection for analysis

**Interpretation:** A score near 1.0 means the answer closely mirrors the retrieved text. A score near 0.0 suggests the model may have generated content not supported by the documents.

---

### 6. Evaluation Harness

The eval harness (`/admin/eval`) runs a test set of Q&A pairs through every combination of:
- Chunking strategy: `fixed`, `recursive`, `semantic`
- Embedding model: `all-MiniLM-L6-v2`, `BAAI/bge-large-en-v1.5`

For each combination it computes:

**Retrieval Precision@k** = (relevant chunks in top-k) / k
- Measures how many of the retrieved chunks are actually relevant.

**Retrieval Recall@k** = (relevant chunks in top-k) / (total relevant chunks)
- Measures how many of the relevant chunks were found.

**Answer Groundedness** = average groundedness score across all test queries.

Results are stored in MongoDB (`eval_results` collection) and displayed in the Admin Dashboard as a table and bar chart.

---

## MongoDB Collections

| Collection | Purpose |
|---|---|
| `users` | Google OAuth user profiles |
| `documents` | Ingested document metadata |
| `chat_history` | All queries, answers, and metadata per session |
| `eval_results` | Evaluation run results per strategy/model combo |
| `flagged_responses` | Low-groundedness answers for analysis |

---

## Configuration Reference

All settings are in `.env` (see `.env.example`):

| Key | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Active embedding model |
| `CHUNKING_STRATEGY` | `fixed` | Active chunking strategy |
| `CHUNK_SIZE` | `512` | Characters per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `TOP_K` | `5` | Chunks retrieved per query |
| `GROUNDEDNESS_THRESHOLD` | `0.4` | Flag threshold |
| `GROQ_API_KEY` | — | Groq API key |
| `MONGODB_URI` | — | MongoDB Atlas connection string |
| `GOOGLE_CLIENT_ID` | — | Google OAuth client ID |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest` | Upload + chunk + embed + store document |
| `POST` | `/query` | Full RAG pipeline query |
| `GET` | `/admin/eval` | Fetch stored eval results |
| `POST` | `/admin/eval` | Trigger evaluation harness |
| `GET` | `/auth/login` | Initiate Google OAuth |
| `GET` | `/auth/callback` | OAuth callback |
| `GET` | `/health` | Health check |

---

## Project Structure

```
mokomax-ai/
├── backend/
│   ├── app/
│   │   ├── config.py              # Pydantic settings
│   │   ├── main.py                # FastAPI app
│   │   ├── db/mongo.py            # MongoDB client
│   │   ├── rag/
│   │   │   ├── extractor.py       # PDF/DOCX/TXT extraction
│   │   │   ├── chunker.py         # 3 chunking strategies
│   │   │   ├── embedder.py        # Swappable embeddings
│   │   │   ├── vector_store.py    # ChromaDB wrapper
│   │   │   └── generator.py       # Groq LLaMA3 generation
│   │   ├── nlp/
│   │   │   ├── intent_classifier.py  # TF-IDF + LR classifier
│   │   │   ├── query_rewriter.py     # LLM-based rewriter
│   │   │   ├── groundedness.py       # NLI + embedding check
│   │   │   └── evaluator.py          # Eval harness
│   │   └── routes/
│   │       ├── ingest.py, query.py, admin.py, auth.py
│   ├── eval_data/test_set.json
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/ChatPage.jsx, AdminPage.jsx
        ├── components/ChatMessage.jsx, GroundednessBadge.jsx,
        │             SourceCitations.jsx, UploadPanel.jsx
        └── api/client.js
```
