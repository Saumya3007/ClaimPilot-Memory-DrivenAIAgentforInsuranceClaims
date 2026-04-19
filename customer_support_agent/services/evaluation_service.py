import logging
import json
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EvaluationMetricsService:
    """
    Evaluates the 'Human-Approved -> Memory' loop.
    """
    
    def __init__(self, metrics_file: str = "data/evaluation_metrics.json"):
        self.metrics_file = metrics_file
        self._metrics = self._load_metrics()

    def _load_metrics(self) -> Dict[str, Any]:
        try:
            with open(self.metrics_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "total_drafts_generated": 0,
                "total_drafts_approved": 0,
                "total_edits_count": 0,
                "total_memory_hits": 0,
                "memory_relevance_scores": [],
                "human_fidelity_scores": [], # 1.0 - (edit_distance / length)
                "history": []
            }

    def _save_metrics(self):
        with open(self.metrics_file, "w") as f:
            json.dump(self._metrics, f, indent=2)

    def log_generation(self, ticket_id: str, memory_hits_count: int):
        self._metrics["total_drafts_generated"] += 1
        self._metrics["total_memory_hits"] += memory_hits_count
        self._save_metrics()

    def log_approval(self, ticket_id: str, original_draft: str, approved_draft: str, memory_used: List[Dict[str, Any]]):
        self._metrics["total_drafts_approved"] += 1
        
        # Calculate Fidelity (Simple string similarity for now)
        fidelity = self._calculate_similarity(original_draft, approved_draft)
        self._metrics["human_fidelity_scores"].append(fidelity)
        
        if original_draft.strip() != approved_draft.strip():
            self._metrics["total_edits_count"] += 1
            
        # Log to history
        self._metrics["history"].append({
            "timestamp": time.time(),
            "ticket_id": ticket_id,
            "fidelity": fidelity,
            "memory_hits": len(memory_used)
        })
        self._save_metrics()

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        if not s1 or not s2: return 0.0
        # Simple Jaccard similarity of words for speed
        w1 = set(s1.lower().split())
        w2 = set(s2.lower().split())
        if not w1 or not w2: return 0.0
        return len(w1 & w2) / len(w1 | w2)

    def get_summary(self) -> Dict[str, Any]:
        count = len(self._metrics["human_fidelity_scores"])
        avg_fidelity = sum(self._metrics["human_fidelity_scores"]) / count if count > 0 else 0
        acceptance_rate = (self._metrics["total_drafts_approved"] / self._metrics["total_drafts_generated"]) if self._metrics["total_drafts_generated"] > 0 else 0
        
        return {
            "avg_human_fidelity": round(avg_fidelity, 4),
            "acceptance_rate": round(acceptance_rate, 4),
            "total_memories_stored": len(self._metrics["history"]),
            "memory_hit_ratio": round(self._metrics["total_memory_hits"] / self._metrics["total_drafts_generated"], 2) if self._metrics["total_drafts_generated"] > 0 else 0
        }

_eval_service = EvaluationMetricsService()

def get_eval_service() -> EvaluationMetricsService:
    return _eval_service
