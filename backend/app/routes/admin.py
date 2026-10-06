import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.nlp.evaluator import run_evaluation

router = APIRouter()
logger = logging.getLogger(__name__)


class EvalRequest(BaseModel):
    corpus_text: str
    test_items: List[Dict[str, Any]]


@router.post("/admin/eval")
async def trigger_eval(req: EvalRequest):
    if not req.test_items:
        raise HTTPException(status_code=400, detail="test_items cannot be empty")
    results = await run_evaluation(req.test_items, req.corpus_text)
    return {"status": "completed", "results": results}


@router.get("/admin/eval")
async def get_eval_results():
    return {"results": []}
