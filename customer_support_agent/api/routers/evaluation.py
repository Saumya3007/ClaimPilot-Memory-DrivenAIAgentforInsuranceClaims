from fastapi import APIRouter
from customer_support_agent.services.evaluation_service import get_eval_service

router = APIRouter()

@router.get("/api/evaluation/summary")
def get_evaluation_summary():
    """
    Returns a summary of the 'Human-Approved -> Memory' feedback loop quality.
    """
    return get_eval_service().get_summary()

@router.get("/api/evaluation/history")
def get_evaluation_history():
    """
    Returns the raw history of claim evaluations and human fidelity scores.
    """
    return get_eval_service()._metrics.get("history", [])
