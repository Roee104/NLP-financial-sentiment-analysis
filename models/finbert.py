# models/finbert.py
"""
FinBERT wrapper: loads the ProsusAI/finbert model and tokenizer,
provides a .predict(text_list) method returning label + confidence for each.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class FinBERT:
    def __init__(self, device=None):
        # Select device: GPU if available, else CPU
        self.device = device or (
            "cuda" if torch.cuda.is_available() else "cpu")
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "ProsusAI/finbert")
        # Move model to device
        self.model.to(self.device).eval()
        # Mapping from model outputs to labels
        self.id2label = {0: "NEG", 1: "NEU", 2: "POS"}

    @torch.inference_mode()
    def predict(self, texts):
        """
        Predict sentiment for a list of texts.
        Returns a list of dicts: [{"label": str, "confidence": float}, ...]
        """
        # Tokenize inputs
        enc = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        # Forward pass
        outputs = self.model(**enc)
        logits = outputs.logits
        # Softmax to probabilities
        probs = torch.softmax(logits, dim=-1).cpu().tolist()
        results = []
        for prob in probs:
            # find index of max probability
            idx = int(max(range(len(prob)), key=lambda i: prob[i]))
            label = self.id2label[idx]
            confidence = round(prob[idx] * 100, 2)
            results.append({"label": label, "confidence": confidence})
        return results
