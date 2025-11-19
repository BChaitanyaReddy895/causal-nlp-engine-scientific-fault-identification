"""Integration tests for verification pipeline."""

import json
from backend.causal_extractor.extractor import CausalExtractor
from backend.kg.kg_manager import KGManager
from backend.verifier.pipeline import create_verification_pipeline
from backend.verifier.counterfactual import analyze_claim_causality


def test_causal_extraction():
    """Test causal triple extraction."""
    extractor = CausalExtractor()
    text = "Turmeric contains curcumin which inhibits COX-2 enzyme"
    triples = extractor.extract(text)
    assert len(triples) > 0
    assert all('subject' in t and 'relation' in t and 'object' in t for t in triples)


def test_kg_initialization():
    """Test knowledge graph initialization."""
    kg = KGManager(":memory:")  # Use in-memory DB for testing
    kg.add_node("test_001", "Test Entity", "compound")
    kg.add_edge("test_001", "test_002", "causes", 0.85)
    
    results = kg.search_node("Test")
    assert len(results) > 0


def test_verification_pipeline():
    """Test full verification pipeline."""
    extractor = CausalExtractor()
    kg = KGManager(":memory:")
    pipeline = create_verification_pipeline(extractor, kg)
    
    claim = "Aspirin reduces pain"
    result = pipeline.verify(claim)
    
    assert 'verdict' in result
    assert 'confidence' in result
    assert result['confidence'] >= 0 and result['confidence'] <= 1


def test_counterfactual_analysis():
    """Test counterfactual reasoning."""
    claim = "Drug X treats disease Y"
    triples = [{"subject": "Drug X", "relation": "treats", "object": "disease Y"}]
    evidence = [{"relevance_score": 0.7}]
    
    analysis = analyze_claim_causality(claim, triples, evidence)
    assert 'counterfactual_analysis' in analysis
    assert 'effect_sizes' in analysis
    assert 'detected_fallacies' in analysis


def test_fallacy_detection():
    """Test fallacy detection in claims."""
    from backend.verifier.counterfactual import FallacyDetector
    
    detector = FallacyDetector()
    claim = "A causes B because A and B both occurred"
    evidence = [{"relevance_score": 0.3}]
    
    fallacies = detector.detect_fallacies(claim, evidence)
    assert len(fallacies) > 0
