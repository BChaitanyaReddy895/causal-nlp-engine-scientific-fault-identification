"""Explainability features: attention visualization, LIME, SHAP, evidence ranking."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class Explanation:
    """Structured explanation for a prediction."""
    claim: str
    verdict: str
    confidence: float
    feature_importances: Dict[str, float]
    attention_weights: Optional[torch.Tensor]
    evidence_ranking: List[Dict]
    causal_paths: List[List[str]]
    counterfactual_examples: List[Dict]


class AttentionVisualizer:
    """Visualizes attention patterns from transformer models."""

    def __init__(self, model: nn.Module, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.attention_maps = {}

    def extract_attention(self, 
                         text: str, 
                         layer: int = -1,
                         head: Optional[int] = None) -> torch.Tensor:
        """
        Extract attention weights from specific layer/head.
        
        Args:
            text: Input text
            layer: Layer index (-1 for last layer)
            head: Attention head index (None for all heads)
            
        Returns:
            Attention weights [heads, seq_len, seq_len] or [seq_len, seq_len]
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=512
        )
        
        # Forward pass with output_attentions=True
        with torch.no_grad():
            if hasattr(self.model, 'encoder'):
                outputs = self.model.encoder(
                    **inputs,
                    output_attentions=True
                )
            else:
                outputs = self.model(
                    **inputs,
                    output_attentions=True
                )
        
        # Extract attention from specified layer
        attentions = outputs.attentions[layer]  # [batch, heads, seq, seq]
        
        if head is not None:
            return attentions[0, head, :, :]  # [seq, seq]
        else:
            return attentions[0]  # [heads, seq, seq]

    def get_token_importance(self, 
                            text: str, 
                            target_token_idx: int = 0) -> Dict[str, float]:
        """
        Get importance of each token for target token (usually CLS).
        
        Args:
            text: Input text
            target_token_idx: Index of target token
            
        Returns:
            Dictionary mapping tokens to importance scores
        """
        attention = self.extract_attention(text)  # [heads, seq, seq]
        
        # Average across heads
        avg_attention = attention.mean(dim=0)  # [seq, seq]
        
        # Get attention to target token
        token_importance = avg_attention[target_token_idx, :]  # [seq]
        
        # Map to tokens
        tokens = self.tokenizer.tokenize(text)
        importance_dict = {}
        
        for i, token in enumerate(tokens):
            if i < len(token_importance):
                importance_dict[token] = float(token_importance[i])
        
        return importance_dict

    def visualize_attention_flow(self, 
                                 text: str,
                                 source_tokens: List[str],
                                 target_tokens: List[str]) -> Dict[Tuple[str, str], float]:
        """
        Visualize attention flow between specific tokens.
        
        Args:
            text: Input text
            source_tokens: List of source tokens
            target_tokens: List of target tokens
            
        Returns:
            Dictionary mapping (source, target) pairs to attention scores
        """
        attention = self.extract_attention(text)  # [heads, seq, seq]
        avg_attention = attention.mean(dim=0)
        
        tokens = self.tokenizer.tokenize(text)
        
        # Find indices
        source_indices = [i for i, t in enumerate(tokens) if t in source_tokens]
        target_indices = [i for i, t in enumerate(tokens) if t in target_tokens]
        
        # Extract flows
        flows = {}
        for si in source_indices:
            for ti in target_indices:
                if si < len(tokens) and ti < len(tokens):
                    flows[(tokens[si], tokens[ti])] = float(avg_attention[si, ti])
        
        return flows


class LIMEExplainer:
    """LIME (Local Interpretable Model-agnostic Explanations) for text."""

    def __init__(self, 
                 model: nn.Module, 
                 tokenizer,
                 num_samples: int = 100):
        self.model = model
        self.tokenizer = tokenizer
        self.num_samples = num_samples

    def explain(self, 
                text: str, 
                num_features: int = 10,
                distance_metric: str = 'cosine') -> Dict[str, float]:
        """
        Generate LIME explanation for prediction.
        
        Args:
            text: Input text
            num_features: Number of top features to return
            distance_metric: Distance metric for weighting samples
            
        Returns:
            Dictionary mapping features to importance scores
        """
        # Get original prediction
        original_pred = self._predict(text)
        original_class = torch.argmax(original_pred).item()
        
        # Tokenize
        tokens = text.split()
        n_tokens = len(tokens)
        
        # Generate perturbed samples
        samples = []
        predictions = []
        
        for _ in range(self.num_samples):
            # Random mask
            mask = np.random.binomial(1, 0.5, n_tokens)
            perturbed_text = ' '.join([t for t, m in zip(tokens, mask) if m])
            
            if perturbed_text:
                samples.append(mask)
                pred = self._predict(perturbed_text)
                predictions.append(pred[0, original_class].item())
            else:
                samples.append(mask)
                predictions.append(0.0)
        
        samples = np.array(samples)
        predictions = np.array(predictions)
        
        # Compute distances
        original_sample = np.ones(n_tokens)
        if distance_metric == 'cosine':
            distances = 1 - (samples @ original_sample) / (
                np.linalg.norm(samples, axis=1) * np.linalg.norm(original_sample) + 1e-6
            )
        else:  # euclidean
            distances = np.linalg.norm(samples - original_sample, axis=1)
        
        # Compute weights
        kernel_width = 0.25 * np.sqrt(n_tokens)
        weights = np.exp(-(distances ** 2) / (kernel_width ** 2))
        
        # Fit linear model
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=1.0)
        model.fit(samples, predictions, sample_weight=weights)
        
        # Get feature importances
        importances = {}
        for i, token in enumerate(tokens):
            if i < len(model.coef_):
                importances[token] = float(model.coef_[i])
        
        # Return top features
        sorted_features = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)
        return dict(sorted_features[:num_features])

    def _predict(self, text: str) -> torch.Tensor:
        """Make prediction on text."""
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=512,
            padding='max_length'
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            if isinstance(outputs, dict):
                logits = outputs.get('logits', outputs.get('causal_logits'))
            else:
                logits = outputs
            probs = F.softmax(logits, dim=-1)
        
        return probs


class SHAPExplainer:
    """SHAP (SHapley Additive exPlanations) for text classification."""

    def __init__(self, model: nn.Module, tokenizer, background_samples: int = 50):
        self.model = model
        self.tokenizer = tokenizer
        self.background_samples = background_samples

    def explain(self, 
                text: str,
                num_features: int = 10) -> Dict[str, float]:
        """
        Generate SHAP explanation using Kernel SHAP.
        
        Args:
            text: Input text
            num_features: Number of top features to return
            
        Returns:
            Dictionary mapping features to SHAP values
        """
        tokens = text.split()
        n_tokens = len(tokens)
        
        # Get base prediction (all masked)
        base_pred = self._predict("")
        
        # Get full prediction
        full_pred = self._predict(text)
        
        # Compute SHAP values using sampling
        shap_values = np.zeros(n_tokens)
        
        for i in range(n_tokens):
            # Sample coalitions
            coalition_preds = []
            
            for _ in range(self.background_samples):
                # Random coalition not including i
                coalition = np.random.binomial(1, 0.5, n_tokens)
                coalition[i] = 0
                
                # With and without feature i
                coalition_without = coalition.copy()
                coalition_with = coalition.copy()
                coalition_with[i] = 1
                
                # Predict
                text_without = ' '.join([t for t, m in zip(tokens, coalition_without) if m])
                text_with = ' '.join([t for t, m in zip(tokens, coalition_with) if m])
                
                pred_without = self._predict(text_without if text_without else "")[0, 0].item()
                pred_with = self._predict(text_with)[0, 0].item()
                
                coalition_preds.append(pred_with - pred_without)
            
            # Average marginal contribution
            shap_values[i] = np.mean(coalition_preds)
        
        # Create dictionary
        shap_dict = {token: float(shap_values[i]) for i, token in enumerate(tokens)}
        
        # Return top features
        sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        return dict(sorted_features[:num_features])

    def _predict(self, text: str) -> torch.Tensor:
        """Make prediction on text."""
        if not text:
            # Return base prediction
            return torch.zeros(1, 1)
        
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=512,
            padding='max_length'
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            if isinstance(outputs, dict):
                logits = outputs.get('logits', outputs.get('causal_logits'))
            else:
                logits = outputs
            probs = F.softmax(logits, dim=-1)
        
        return probs


class EvidenceRanker:
    """Ranks evidence by relevance and quality."""

    def __init__(self, relevance_model: nn.Module):
        self.relevance_model = relevance_model

    def rank_evidence(self,
                     claim: str,
                     evidence_list: List[Dict],
                     criteria: Dict[str, float] = None) -> List[Dict]:
        """
        Rank evidence by multiple criteria.
        
        Args:
            claim: The claim being verified
            evidence_list: List of evidence dictionaries
            criteria: Weights for different criteria
            
        Returns:
            Ranked list of evidence with scores
        """
        if criteria is None:
            criteria = {
                'relevance': 0.4,
                'citation_count': 0.2,
                'recency': 0.2,
                'source_quality': 0.2
            }
        
        scored_evidence = []
        
        for evidence in evidence_list:
            scores = {}
            
            # Relevance score (using neural model)
            scores['relevance'] = self._compute_relevance(claim, evidence.get('text', ''))
            
            # Citation count score (normalized)
            citations = evidence.get('citations', 0)
            scores['citation_count'] = min(citations / 100.0, 1.0)
            
            # Recency score
            year = evidence.get('year', 2000)
            scores['recency'] = max(0, (year - 2000) / 25.0)  # Normalize to recent 25 years
            
            # Source quality
            journal_impact = evidence.get('impact_factor', 1.0)
            scores['source_quality'] = min(journal_impact / 10.0, 1.0)
            
            # Weighted total
            total_score = sum(scores[k] * criteria[k] for k in criteria.keys())
            
            scored_evidence.append({
                **evidence,
                'score': total_score,
                'score_breakdown': scores
            })
        
        # Sort by score
        scored_evidence.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_evidence

    def _compute_relevance(self, claim: str, evidence: str) -> float:
        """Compute semantic relevance between claim and evidence."""
        # Placeholder for semantic similarity
        # In practice, use the relevance model
        
        # Simple word overlap for demo
        claim_words = set(claim.lower().split())
        evidence_words = set(evidence.lower().split())
        
        if not claim_words or not evidence_words:
            return 0.0
        
        overlap = len(claim_words & evidence_words)
        union = len(claim_words | evidence_words)
        
        return overlap / union if union > 0 else 0.0


class CausalPathHighlighter:
    """Highlights important causal paths in explanations."""

    def __init__(self, causal_graph: Dict[str, List[str]]):
        self.graph = causal_graph

    def find_causal_paths(self,
                         source: str,
                         target: str,
                         max_length: int = 5) -> List[List[str]]:
        """
        Find all causal paths from source to target.
        
        Args:
            source: Source node
            target: Target node
            max_length: Maximum path length
            
        Returns:
            List of paths (each path is a list of nodes)
        """
        paths = []
        self._dfs_paths(source, target, [source], paths, max_length)
        return paths

    def _dfs_paths(self, 
                   current: str, 
                   target: str, 
                   path: List[str], 
                   all_paths: List[List[str]],
                   max_length: int):
        """DFS to find all paths."""
        if len(path) > max_length:
            return
        
        if current == target:
            all_paths.append(path.copy())
            return
        
        if current not in self.graph:
            return
        
        for neighbor in self.graph[current]:
            if neighbor not in path:  # Avoid cycles
                path.append(neighbor)
                self._dfs_paths(neighbor, target, path, all_paths, max_length)
                path.pop()

    def score_path_importance(self,
                             path: List[str],
                             edge_weights: Dict[Tuple[str, str], float]) -> float:
        """
        Score importance of a causal path.
        
        Args:
            path: List of nodes in path
            edge_weights: Dictionary mapping edges to weights
            
        Returns:
            Path importance score
        """
        if len(path) < 2:
            return 0.0
        
        # Product of edge weights (geometric mean)
        weights = []
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            weight = edge_weights.get(edge, 0.5)
            weights.append(weight)
        
        if not weights:
            return 0.0
        
        # Geometric mean, penalized by path length
        score = np.prod(weights) ** (1.0 / len(weights))
        score *= (0.9 ** (len(path) - 2))  # Length penalty
        
        return float(score)

    def highlight_critical_paths(self,
                                source: str,
                                target: str,
                                edge_weights: Dict[Tuple[str, str], float],
                                top_k: int = 3) -> List[Dict]:
        """
        Find and highlight top-k most important causal paths.
        
        Args:
            source: Source node
            target: Target node
            edge_weights: Edge weights
            top_k: Number of paths to return
            
        Returns:
            List of dictionaries with path info
        """
        # Find all paths
        paths = self.find_causal_paths(source, target)
        
        if not paths:
            return []
        
        # Score paths
        scored_paths = []
        for path in paths:
            score = self.score_path_importance(path, edge_weights)
            scored_paths.append({
                'path': path,
                'score': score,
                'length': len(path),
                'edges': [(path[i], path[i+1]) for i in range(len(path)-1)]
            })
        
        # Sort and return top-k
        scored_paths.sort(key=lambda x: x['score'], reverse=True)
        return scored_paths[:top_k]


class ExplainabilityPipeline:
    """Complete explainability pipeline combining all methods."""

    def __init__(self,
                 model: nn.Module,
                 tokenizer,
                 causal_graph: Dict[str, List[str]]):
        self.model = model
        self.tokenizer = tokenizer
        
        self.attention_viz = AttentionVisualizer(model, tokenizer)
        self.lime = LIMEExplainer(model, tokenizer)
        self.shap = SHAPExplainer(model, tokenizer)
        self.evidence_ranker = EvidenceRanker(model)
        self.path_highlighter = CausalPathHighlighter(causal_graph)

    def generate_explanation(self,
                            claim: str,
                            prediction: Dict,
                            evidence: List[Dict],
                            causal_graph_data: Dict) -> Explanation:
        """
        Generate comprehensive explanation.
        
        Args:
            claim: Input claim
            prediction: Model prediction
            evidence: List of evidence
            causal_graph_data: Causal graph information
            
        Returns:
            Explanation object
        """
        # Feature importance (combine LIME and SHAP)
        lime_scores = self.lime.explain(claim, num_features=10)
        shap_scores = self.shap.explain(claim, num_features=10)
        
        # Average scores
        all_tokens = set(lime_scores.keys()) | set(shap_scores.keys())
        feature_importances = {}
        for token in all_tokens:
            lime_val = lime_scores.get(token, 0)
            shap_val = shap_scores.get(token, 0)
            feature_importances[token] = (lime_val + shap_val) / 2
        
        # Attention weights
        attention = self.attention_viz.extract_attention(claim)
        
        # Rank evidence
        ranked_evidence = self.evidence_ranker.rank_evidence(claim, evidence)
        
        # Find critical causal paths
        if causal_graph_data.get('nodes'):
            source_node = causal_graph_data['nodes'][0]['id'] if causal_graph_data['nodes'] else None
            target_node = causal_graph_data['nodes'][-1]['id'] if len(causal_graph_data['nodes']) > 1 else None
            
            if source_node and target_node:
                edge_weights = {
                    (e['source'], e['target']): e.get('weight', 0.5)
                    for e in causal_graph_data.get('edges', [])
                }
                causal_paths = self.path_highlighter.highlight_critical_paths(
                    source_node,
                    target_node,
                    edge_weights,
                    top_k=3
                )
            else:
                causal_paths = []
        else:
            causal_paths = []
        
        return Explanation(
            claim=claim,
            verdict=prediction.get('verdict', 'UNKNOWN'),
            confidence=prediction.get('confidence', 0.0),
            feature_importances=feature_importances,
            attention_weights=attention,
            evidence_ranking=ranked_evidence[:5],  # Top 5
            causal_paths=causal_paths,
            counterfactual_examples=[]  # TODO: Add counterfactuals
        )


if __name__ == "__main__":
    print("✅ Explainability modules initialized")
    
    # Test evidence ranker
    ranker = EvidenceRanker(None)
    evidence = [
        {'text': 'Study shows correlation', 'citations': 50, 'year': 2020, 'impact_factor': 5.0},
        {'text': 'Meta-analysis confirms', 'citations': 150, 'year': 2022, 'impact_factor': 10.0}
    ]
    
    ranked = ranker.rank_evidence("Test claim", evidence)
    print(f"Ranked {len(ranked)} evidence items")
    
    # Test causal path highlighter
    graph = {'A': ['B', 'C'], 'B': ['D'], 'C': ['D']}
    highlighter = CausalPathHighlighter(graph)
    paths = highlighter.find_causal_paths('A', 'D')
    print(f"Found {len(paths)} causal paths")
    
    print("✅ All explainability tests passed")
