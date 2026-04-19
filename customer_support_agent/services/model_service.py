import logging
from typing import Dict, Any
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

class InsuranceModelService:
    """
    Specific model implementations for insurance tasks:
    1. RoBERTa for Sentiment Analysis (Claimant urgency/frustration)
    2. BERT for Claim Categorization
    """
    
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Initializing InsuranceModelService on device: {self.device}")
        
        # RoBERTa for sentiment/urgency
        try:
            self.sentiment_pipe = pipeline(
                "sentiment-analysis", 
                model="cardiffnlp/twitter-roberta-base-sentiment", 
                device=self.device
            )
        except Exception as e:
            logger.warning(f"Failed to load RoBERTa sentiment model: {e}. Falling back to default.")
            self.sentiment_pipe = None

        # BERT for classification (mocking a custom fine-tuned model path or using a general one)
        try:
            # In a real scenario, this would be a local path to a model fine-tuned on insurance data
            self.classifier_pipe = pipeline(
                "zero-shot-classification", 
                model="facebook/bart-large-mnli", 
                device=self.device
            )
        except Exception as e:
            logger.warning(f"Failed to load BART classifier: {e}")
            self.classifier_pipe = None

    def analyze_claim_text(self, description: str) -> Dict[str, Any]:
        """
        Analyze claim description for priority and category.
        """
        results = {
            "urgency_score": 0.5,
            "sentiment": "neutral",
            "category": "general",
            "model_notes": []
        }
        
        if not description or len(description.strip()) < 10:
            return results

        # 1. Sentiment via RoBERTa
        if self.sentiment_pipe:
            try:
                # model outputs: 0 -> Negative, 1 -> Neutral, 2 -> Positive
                sent = self.sentiment_pipe(description[:512])[0]
                label_map = {"LABEL_0": "negative", "LABEL_1": "neutral", "LABEL_2": "positive"}
                results["sentiment"] = label_map.get(sent["label"], sent["label"])
                # Map negative sentiment to higher urgency
                if results["sentiment"] == "negative":
                    results["urgency_score"] = min(1.0, sent["score"] + 0.5)
                results["model_notes"].append(f"RoBERTa sentiment: {results['sentiment']} ({sent['score']:.2f})")
            except Exception as e:
                logger.error(f"RoBERTa inference error: {e}")

        # 2. Category via Zero-shot BERT/BART
        if self.classifier_pipe:
            try:
                candidate_labels = ["auto accident", "theft", "vandalism", "natural disaster", "medical claim"]
                classification = self.classifier_pipe(description[:512], candidate_labels)
                results["category"] = classification["labels"][0]
                results["model_notes"].append(f"BART Category: {results['category']} ({classification['scores'][0]:.2f})")
            except Exception as e:
                logger.error(f"Classifier inference error: {e}")

        return results

# Singleton instance
_model_service = None

def get_model_service() -> InsuranceModelService:
    global _model_service
    if _model_service is None:
        _model_service = InsuranceModelService()
    return _model_service
