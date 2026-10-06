from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    openai_api_key: str = ""

    # Chunking
    chunking_strategy: str = "fixed"
    chunk_size: int = 512
    chunk_overlap: int = 64

    # ChromaDB
    chroma_persist_dir: str = "./chroma_store"

    # MongoDB
    mongodb_uri: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # App
    secret_key: str = "change_me"
    frontend_url: str = "http://localhost:5173"

    # Retrieval
    top_k: int = 5

    # Groundedness threshold for flagging
    groundedness_threshold: float = 0.4

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
