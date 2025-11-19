"""Causal triple extraction module."""

import re
from typing import List, Dict, Tuple
import spacy
from transformers import pipeline

class RuleBasedExtractor:
    """Rule-based causal extraction using spaCy."""

    CAUSAL_KEYWORDS = [
        "cause", "causes", "caused", "leading", "lead", "leads",
        "induce", "induces", "induced", "trigger", "triggers",
        "activate", "activates", "activated", "inhibit", "inhibits",
        "prevent", "prevents", "prevents", "result", "results",
        "produce", "produces", "generated", "generate", "reduce",
        "reduces", "increase", "increases", "accelerate", "accelerates",
        "suppress", "suppresses", "enhance", "enhances", "promote",
        "promotes", "block", "blocks", "impair", "impairs"
    ]

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("⚠️  spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None

    def extract_triples(self, text: str) -> List[Dict]:
        """Extract causal triples using dependency parsing."""
        if not self.nlp:
            return []

        doc = self.nlp(text)
        triples = []

        # Pattern 1: SVO with causal verb (nsubj-verb-obj)
        for token in doc:
            if token.lemma_.lower() in self.CAUSAL_KEYWORDS:
                subj = None
                obj = None
                for child in token.children:
                    if child.dep_ == "nsubj":
                        subj = child.text
                    elif child.dep_ in ["obj", "attr"]:
                        obj = child.text

                if subj and obj:
                    triples.append({
                        "subject": subj,
                        "relation": token.text,
                        "object": obj,
                        "confidence": 0.75,
                        "method": "rule_based"
                    })

        return triples


class TransformerExtractor:
    """Transformer-based extraction (T5/DeBERTa)."""

    def __init__(self, model_name: str = "t5-small"):
        try:
            self.nlp_model = pipeline("text2text-generation", model=model_name)
        except:
            self.nlp_model = None
            print(f"⚠️  Model {model_name} not available offline")

    def extract_triples(self, text: str) -> List[Dict]:
        """Extract causal triples using transformer."""
        if not self.nlp_model:
            return []

        prompt = f"Extract causal triples from: {text}\nFormat: subject | relation | object"
        try:
            results = self.nlp_model(prompt, max_length=100)
            output = results[0]["generated_text"]
            # Parse output and create triples
            triples = []
            for line in output.split('\n'):
                parts = line.split('|')
                if len(parts) == 3:
                    triples.append({
                        "subject": parts[0].strip(),
                        "relation": parts[1].strip(),
                        "object": parts[2].strip(),
                        "confidence": 0.65,
                        "method": "transformer"
                    })
            return triples
        except:
            return []


class CausalExtractor:
    """Combined causal extractor."""

    def __init__(self):
        self.rule_extractor = RuleBasedExtractor()
        self.transformer_extractor = TransformerExtractor()

    def extract(self, text: str) -> List[Dict]:
        """Extract triples using ensemble method."""
        rule_triples = self.rule_extractor.extract_triples(text)
        transformer_triples = self.transformer_extractor.extract_triples(text)

        # Combine and deduplicate
        all_triples = rule_triples + transformer_triples
        unique_triples = []
        seen = set()

        for triple in all_triples:
            key = (triple["subject"].lower(), triple["relation"].lower(), triple["object"].lower())
            if key not in seen:
                unique_triples.append(triple)
                seen.add(key)

        return unique_triples


if __name__ == "__main__":
    extractor = CausalExtractor()
    test_text = "Turmeric contains curcumin which inhibits COX-2 enzyme, thereby reducing inflammation."
    triples = extractor.extract(test_text)
    print(f"Extracted {len(triples)} triples:")
    for t in triples:
        print(f"  {t['subject']} --[{t['relation']}]--> {t['object']} ({t['confidence']:.2f})")
