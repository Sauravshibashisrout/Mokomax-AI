"""Async MongoDB client via Motor."""
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def get_db() -> AsyncIOMotorDatabase:
    global _client
    if _client is None:
        cfg = get_settings()
        _client = AsyncIOMotorClient(cfg.mongodb_uri)
        logger.info("MongoDB client initialised")
    return _client["mokomax"]


# Convenience collection accessors
def users_col():       return get_db()["users"]
def documents_col():   return get_db()["documents"]
def chat_col():        return get_db()["chat_history"]
def eval_col():        return get_db()["eval_results"]
def flagged_col():     return get_db()["flagged_responses"]
