"""Evaluation framework for benchmark testing."""

import json
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path


class EvaluationMetrics:
    """Compute evaluation metrics."""

    @staticmethod
    def precision_recall_f1(predictions: List[str], ground_truth: List[str]) -> Dict:
        """Compute P/R/F1."""
        tp = sum(1 for p, g in zip(predictions, ground_truth) if p == g and g != 'UNVERIFIABLE')
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p != g and g != 'UNVERIFIABLE')
        fn = sum(1 for p, g in zip(predictions, ground_truth) if p != g and p != 'UNVERIFIABLE')

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {"precision": precision, "recall": recall, "f1": f1}

    @staticmethod
    def mean_reciprocal_rank(ranked_results: List[Dict]) -> float:
        """Compute MRR for ranking tasks."""
        mrr = 0
        for result in ranked_results:
            if result.get('relevant'):
                mrr += 1 / (result.get('rank', float('inf')))
        return mrr / len(ranked_results) if ranked_results else 0

    @staticmethod
    def accuracy(predictions: List[str], ground_truth: List[str]) -> float:
        """Compute accuracy."""
        return sum(1 for p, g in zip(predictions, ground_truth) if p == g) / len(predictions)


def evaluate_on_benchmark(model_predictions: List[Dict], ground_truth: List[Dict]) -> Dict:
    """Evaluate on full benchmark."""
    verdicts_pred = [p['verdict'] for p in model_predictions]
    verdicts_true = [g['verdict'] for g in ground_truth]

    metrics = EvaluationMetrics()

    results = {
        "accuracy": metrics.accuracy(verdicts_pred, verdicts_true),
        "p_r_f1": metrics.precision_recall_f1(verdicts_pred, verdicts_true),
        "total_samples": len(verdicts_pred),
        "correct": sum(1 for p, g in zip(verdicts_pred, verdicts_true) if p == g),
        "by_verdict": {}
    }

    # Per-verdict breakdown
    for verdict in set(verdicts_true):
        indices = [i for i, g in enumerate(verdicts_true) if g == verdict]
        if indices:
            verdict_preds = [verdicts_pred[i] for i in indices]
            verdict_true = [verdicts_true[i] for i in indices]
            results["by_verdict"][verdict] = {
                "count": len(indices),
                "accuracy": metrics.accuracy(verdict_preds, verdict_true)
            }

    return results


def save_evaluation_report(results: Dict, output_path: str = "results/evaluation_report.json"):
    """Save evaluation report."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Evaluation report saved to {output_path}")


if __name__ == "__main__":
    # Example evaluation
    predictions = [
        {"verdict": "SUPPORTS_CAUSALITY"},
        {"verdict": "CORRELATION_NOT_CAUSAL"},
        {"verdict": "UNVERIFIABLE"}
    ]
    ground_truth = [
        {"verdict": "SUPPORTS_CAUSALITY"},
        {"verdict": "CORRELATION_NOT_CAUSAL"},
        {"verdict": "REFUTES_CAUSALITY"}
    ]

    results = evaluate_on_benchmark(predictions, ground_truth)
    save_evaluation_report(results)
    print(json.dumps(results, indent=2))
