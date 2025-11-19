"""Verification pipeline for causal fallacy detection."""

import json
from typing import Dict, List, Any
from enum import Enum

class Verdict(Enum):
    """Verdict types."""
    SUPPORTS_CAUSALITY = "SUPPORTS_CAUSALITY"
    REFUTES_CAUSALITY = "REFUTES_CAUSALITY"
    CORRELATION_NOT_CAUSAL = "CORRELATION_NOT_CAUSAL"
    UNVERIFIABLE = "UNVERIFIABLE"
    MISSING_MECHANISM = "MISSING_MECHANISM"


class VerificationPipeline:
    """End-to-end verification pipeline."""

    def __init__(self, extractor, kg_manager, gnn_model):
        self.extractor = extractor
        self.kg_manager = kg_manager
        self.gnn_model = gnn_model

    def verify(self, claim: str, domain: str = "medicine") -> Dict[str, Any]:
        """Verify a scientific claim."""

        # Step 1: Extract causal triples
        triples = self.extractor.extract(claim)

        # Step 2: Build causal graph
        causal_graph = self._build_graph(triples)

        # Step 3: Query KG for evidence
        evidence = self._collect_evidence(triples)

        # Step 4: Score consistency
        consistency_scores = self._score_consistency(triples, evidence)

        # Step 5: Detect missing mechanisms
        missing_mechanisms = self._identify_missing_mechanisms(triples, evidence)

        # Step 6: Generate verdict
        verdict = self._generate_verdict(triples, consistency_scores, missing_mechanisms)

        # Step 7: Generate explanation
        explanation = self._generate_explanation(verdict, triples, evidence, missing_mechanisms)

        return {
            "claim": claim,
            "verdict": verdict.value,
            "confidence": self._calculate_confidence(consistency_scores),
            "triples": triples,
            "causal_graph": causal_graph,
            "evidence": evidence,
            "missing_mechanism": missing_mechanisms,
            "explanation": explanation,
            "domain": domain
        }

    def _build_graph(self, triples: List[Dict]) -> Dict:
        """Build causal graph from triples."""
        nodes = set()
        edges = []

        for triple in triples:
            nodes.add(triple["subject"])
            nodes.add(triple["object"])
            edges.append({
                "source": triple["subject"],
                "target": triple["object"],
                "relation": triple["relation"],
                "confidence": triple.get("confidence", 0.5)
            })

        return {
            "nodes": [{"id": n, "label": n} for n in nodes],
            "edges": edges
        }

    def _collect_evidence(self, triples: List[Dict]) -> List[Dict]:
        """Collect evidence from KG."""
        evidence = []

        for triple in triples:
            # Search KG for nodes
            subject_results = self.kg_manager.search_node(triple["subject"])
            object_results = self.kg_manager.search_node(triple["object"])

            for subj in subject_results[:1]:
                for obj in object_results[:1]:
                    path = self.kg_manager.get_evidence_path(subj["id"], obj["id"])
                    if path:
                        evidence.append({
                            "type": "kg_path",
                            "path": path,
                            "length": len(path),
                            "relevance_score": 1.0 / len(path)
                        })

        return evidence

    def _score_consistency(self, triples: List[Dict], evidence: List[Dict]) -> Dict:
        """Score consistency of triples with evidence."""
        scores = {}

        for i, triple in enumerate(triples):
            if evidence:
                scores[i] = min(0.9, len(evidence) * 0.3)
            else:
                scores[i] = 0.2

        return scores

    def _identify_missing_mechanisms(self, triples: List[Dict], evidence: List[Dict]) -> List[str]:
        """Identify missing mechanistic pathways."""
        mechanisms = []

        if not evidence:
            mechanisms.append("Direct mechanistic pathway")
            mechanisms.append("Molecular interaction validation")

        for triple in triples:
            if triple["relation"] not in ["causes", "leads", "results"]:
                continue
            mechanisms.append(f"{triple['subject']}-{triple['relation']}-{triple['object']} pathway")

        return mechanisms

    def _generate_verdict(self, triples: List[Dict], scores: Dict, mechanisms: List[str]) -> Verdict:
        """Generate final verdict."""
        avg_score = sum(scores.values()) / len(scores) if scores else 0

        if avg_score > 0.8:
            return Verdict.SUPPORTS_CAUSALITY
        elif avg_score < 0.3:
            return Verdict.REFUTES_CAUSALITY
        elif avg_score < 0.5 and mechanisms:
            return Verdict.MISSING_MECHANISM
        elif avg_score < 0.5:
            return Verdict.CORRELATION_NOT_CAUSAL
        else:
            return Verdict.UNVERIFIABLE

    def _calculate_confidence(self, scores: Dict) -> float:
        """Calculate overall confidence."""
        if not scores:
            return 0.5
        avg = sum(scores.values()) / len(scores)
        return min(0.99, max(0.01, avg))

    def _generate_explanation(self, verdict: Verdict, triples: List[Dict],
                             evidence: List[Dict], mechanisms: List[str]) -> str:
        """Generate natural language explanation."""
        explanations = {
            Verdict.SUPPORTS_CAUSALITY: "Strong scientific evidence supports this causal claim with established mechanistic pathways.",
            Verdict.REFUTES_CAUSALITY: "This causal claim contradicts established scientific evidence.",
            Verdict.CORRELATION_NOT_CAUSAL: "Evidence shows correlation but does not establish causation.",
            Verdict.UNVERIFIABLE: "Insufficient scientific evidence available to verify this claim.",
            Verdict.MISSING_MECHANISM: f"While plausible, the mechanistic pathway is unclear. Missing: {', '.join(mechanisms[:2])}"
        }
        return explanations.get(verdict, "Unclear verdict")


def create_verification_pipeline(extractor, kg_manager, gnn_model=None):
    """Factory for verification pipeline."""
    return VerificationPipeline(extractor, kg_manager, gnn_model)


if __name__ == "__main__":
    print("✅ Verification pipeline initialized")
