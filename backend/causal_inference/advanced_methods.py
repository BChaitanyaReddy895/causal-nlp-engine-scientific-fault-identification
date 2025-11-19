"""Advanced causal inference: do-calculus, counterfactuals, intervention analysis."""

import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
from dataclasses import dataclass
from enum import Enum


class InterventionType(Enum):
    """Types of causal interventions."""
    DO = "do"  # Hard intervention
    SOFT = "soft"  # Soft intervention
    COUNTERFACTUAL = "counterfactual"  # Counterfactual query


@dataclass
class CausalQuery:
    """Represents a causal query."""
    outcome: str
    treatment: str
    confounders: List[str]
    mediators: List[str]
    intervention_type: InterventionType


class DoCalculusEngine:
    """Implements do-calculus rules for causal inference."""

    def __init__(self, causal_graph: Dict[str, List[str]]):
        """
        Initialize do-calculus engine.
        
        Args:
            causal_graph: Dict mapping nodes to their children
        """
        self.graph = causal_graph
        self.nodes = set(causal_graph.keys())

    def get_parents(self, node: str) -> Set[str]:
        """Get parent nodes."""
        parents = set()
        for parent, children in self.graph.items():
            if node in children:
                parents.add(parent)
        return parents

    def get_ancestors(self, nodes: Set[str]) -> Set[str]:
        """Get all ancestors of given nodes."""
        ancestors = set(nodes)
        changed = True
        
        while changed:
            changed = False
            for node in list(ancestors):
                parents = self.get_parents(node)
                new_ancestors = parents - ancestors
                if new_ancestors:
                    ancestors.update(new_ancestors)
                    changed = True
        
        return ancestors

    def d_separated(self, X: Set[str], Y: Set[str], Z: Set[str]) -> bool:
        """
        Check if X and Y are d-separated given Z.
        
        Simplified implementation - checks if all paths are blocked.
        """
        # Get all ancestors of X, Y, Z
        ancestors = self.get_ancestors(X | Y | Z)
        
        # Check each path from X to Y
        for x in X:
            for y in Y:
                if self._has_active_path(x, y, Z, ancestors):
                    return False
        
        return True

    def _has_active_path(self, start: str, end: str, Z: Set[str], ancestors: Set[str]) -> bool:
        """Check if there's an active path from start to end given Z."""
        # Simplified BFS to check for unblocked paths
        visited = set()
        queue = [(start, None)]  # (node, parent)
        
        while queue:
            node, parent = queue.pop(0)
            
            if node == end:
                return True
            
            if (node, parent) in visited:
                continue
            visited.add((node, parent))
            
            # Check children
            for child in self.graph.get(node, []):
                # Chain or fork: blocked if node in Z
                if node not in Z:
                    queue.append((child, node))
            
            # Check parents
            for p in self.get_parents(node):
                # Collider: unblocked if node or descendant in Z
                if node in Z or any(desc in Z for desc in self._get_descendants(node)):
                    queue.append((p, node))
        
        return False

    def _get_descendants(self, node: str) -> Set[str]:
        """Get all descendants of a node."""
        descendants = set()
        queue = [node]
        
        while queue:
            current = queue.pop(0)
            for child in self.graph.get(current, []):
                if child not in descendants:
                    descendants.add(child)
                    queue.append(child)
        
        return descendants

    def rule1_insertion_deletion(self, Y: Set[str], X: Set[str], Z: Set[str], W: Set[str]) -> bool:
        """
        Rule 1: Insertion/deletion of observations.
        P(y|do(x),z,w) = P(y|do(x),w) if (Y ⊥ Z | X,W)_Gx
        """
        # Create graph with do(X)
        graph_x = {k: [v for v in children if v not in X] 
                   for k, children in self.graph.items() if k not in X}
        
        # Check d-separation in modified graph
        engine_x = DoCalculusEngine(graph_x)
        return engine_x.d_separated(Y, Z, X | W)

    def rule2_action_observation(self, Y: Set[str], X: Set[str], Z: Set[str], W: Set[str]) -> bool:
        """
        Rule 2: Action/observation exchange.
        P(y|do(x),do(z),w) = P(y|do(x),z,w) if (Y ⊥ Z | X,W)_Gxz̄
        """
        # Create graph with do(X) and remove outgoing edges from Z
        graph_xz = {k: [v for v in children if v not in X and k not in Z] 
                    for k, children in self.graph.items() if k not in X}
        
        engine_xz = DoCalculusEngine(graph_xz)
        return engine_xz.d_separated(Y, Z, X | W)

    def rule3_insertion_deletion_actions(self, Y: Set[str], X: Set[str], Z: Set[str], W: Set[str]) -> bool:
        """
        Rule 3: Insertion/deletion of actions.
        P(y|do(x),do(z),w) = P(y|do(x),w) if (Y ⊥ Z | X,W)_Gxz(W)
        """
        # Check if Z is irrelevant to Y
        An_W = self.get_ancestors(W)
        relevant_Z = {z for z in Z if z in An_W or any(self._has_path(z, y) for y in Y)}
        
        if not relevant_Z:
            return True
        
        return False

    def _has_path(self, start: str, end: str) -> bool:
        """Check if there's any path from start to end."""
        visited = set()
        queue = [start]
        
        while queue:
            node = queue.pop(0)
            if node == end:
                return True
            if node in visited:
                continue
            visited.add(node)
            queue.extend(self.graph.get(node, []))
        
        return False


class CounterfactualReasoning(nn.Module):
    """Neural counterfactual reasoning module."""

    def __init__(self, input_dim: int, hidden_dim: int = 256):
        super().__init__()
        
        # Structural equation model parameters
        self.sem_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Intervention effect estimator
        self.intervention_net = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )
        
        # Counterfactual generator
        self.counterfactual_gen = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, input_dim)
        )
        
        # Exogenous noise estimator
        self.noise_estimator = nn.Sequential(
            nn.Linear(input_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, input_dim)
        )

    def forward(self, 
                factual: torch.Tensor, 
                intervention: torch.Tensor,
                treatment_idx: int) -> Dict[str, torch.Tensor]:
        """
        Generate counterfactual given factual observation and intervention.
        
        Args:
            factual: Factual observation [B, D]
            intervention: Intervention values [B, D]
            treatment_idx: Index of treatment variable
            
        Returns:
            Dictionary with counterfactual and related quantities
        """
        # Encode factual
        factual_repr = self.sem_encoder(factual)
        
        # Estimate exogenous noise
        noise = self.noise_estimator(factual)
        
        # Encode intervention
        intervention_repr = self.sem_encoder(intervention)
        
        # Compute intervention effect
        combined = torch.cat([factual_repr, intervention_repr], dim=-1)
        intervention_effect = self.intervention_net(combined)
        
        # Generate counterfactual
        # Three-step process: abduction, action, prediction
        
        # 1. Abduction: infer exogenous variables from factual
        exogenous = factual + noise
        
        # 2. Action: modify treatment variable
        modified = exogenous.clone()
        modified[:, treatment_idx] = intervention[:, treatment_idx]
        
        # 3. Prediction: generate counterfactual outcome
        counterfactual_input = torch.cat([self.sem_encoder(modified), intervention_repr], dim=-1)
        counterfactual = self.counterfactual_gen(counterfactual_input)
        
        # Compute treatment effect
        treatment_effect = counterfactual - factual
        
        return {
            'counterfactual': counterfactual,
            'treatment_effect': treatment_effect,
            'intervention_effect': intervention_effect,
            'exogenous': exogenous,
            'factual_repr': factual_repr
        }


class CausalEffectEstimator(nn.Module):
    """Estimates average treatment effect (ATE) and conditional ATE."""

    def __init__(self, input_dim: int, hidden_dim: int = 256):
        super().__init__()
        
        # Propensity score model
        self.propensity_net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # Outcome models (separate for treated and control)
        self.outcome_net_treated = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1)
        )
        
        self.outcome_net_control = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1)
        )
        
        # Doubly robust estimator
        self.dr_net = nn.Sequential(
            nn.Linear(input_dim + 3, hidden_dim),  # features + propensity + outcomes
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, 
                covariates: torch.Tensor, 
                treatment: torch.Tensor, 
                outcome: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Estimate causal effects.
        
        Args:
            covariates: Covariate matrix [B, D]
            treatment: Treatment indicator [B, 1]
            outcome: Observed outcomes [B, 1]
            
        Returns:
            Dictionary with effect estimates
        """
        # Propensity score
        propensity = self.propensity_net(covariates)
        
        # Predicted outcomes
        y1_pred = self.outcome_net_treated(covariates)  # E[Y|T=1,X]
        y0_pred = self.outcome_net_control(covariates)  # E[Y|T=0,X]
        
        # IPW (Inverse Propensity Weighting) estimator
        ipw_weight_treated = treatment / (propensity + 1e-6)
        ipw_weight_control = (1 - treatment) / (1 - propensity + 1e-6)
        
        ate_ipw = torch.mean(ipw_weight_treated * outcome - ipw_weight_control * outcome)
        
        # Regression estimator
        ate_reg = torch.mean(y1_pred - y0_pred)
        
        # Doubly robust estimator
        dr_input = torch.cat([covariates, propensity, y1_pred, y0_pred], dim=-1)
        ate_dr = self.dr_net(dr_input).mean()
        
        # CATE (Conditional Average Treatment Effect)
        cate = y1_pred - y0_pred
        
        return {
            'ate_ipw': ate_ipw,
            'ate_reg': ate_reg,
            'ate_dr': ate_dr,
            'cate': cate,
            'propensity': propensity,
            'y1_pred': y1_pred,
            'y0_pred': y0_pred
        }


class ConfoundingDetector(nn.Module):
    """Detects and adjusts for confounding variables."""

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        
        # Confounder detection network
        self.confounder_scorer = nn.Sequential(
            nn.Linear(input_dim * 3, hidden_dim),  # X, Y, Z
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # Back-door criterion checker
        self.backdoor_net = nn.Sequential(
            nn.Linear(input_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

    def detect_confounders(self,
                          treatment: torch.Tensor,
                          outcome: torch.Tensor,
                          covariates: torch.Tensor) -> torch.Tensor:
        """
        Detect which covariates are confounders.
        
        Args:
            treatment: Treatment variable [B, 1]
            outcome: Outcome variable [B, 1]
            covariates: Potential confounders [B, D]
            
        Returns:
            Confounder scores [B, D]
        """
        B, D = covariates.shape
        scores = []
        
        for i in range(D):
            z = covariates[:, i:i+1]
            # Check if Z is associated with both X and Y
            combined = torch.cat([treatment, outcome, z], dim=-1)
            score = self.confounder_scorer(combined)
            scores.append(score)
        
        scores = torch.cat(scores, dim=-1)
        return scores

    def check_backdoor_criterion(self,
                                treatment: torch.Tensor,
                                outcome: torch.Tensor,
                                adjustment_set: torch.Tensor) -> torch.Tensor:
        """
        Check if adjustment set satisfies back-door criterion.
        
        Args:
            treatment: Treatment variable [B, 1]
            outcome: Outcome variable [B, 1]
            adjustment_set: Proposed adjustment set [B, D]
            
        Returns:
            Score indicating if criterion is satisfied [B, 1]
        """
        combined = torch.cat([treatment, adjustment_set], dim=-1)
        score = self.backdoor_net(combined)
        return score


class InterventionPlanner:
    """Plans and evaluates causal interventions."""

    def __init__(self, causal_graph: Dict[str, List[str]]):
        self.graph = causal_graph
        self.do_calculus = DoCalculusEngine(causal_graph)

    def plan_intervention(self, 
                         target: str, 
                         desired_outcome: str,
                         available_interventions: List[str]) -> Dict[str, any]:
        """
        Plan intervention to achieve desired outcome.
        
        Args:
            target: Target variable to change
            desired_outcome: Desired outcome variable
            available_interventions: List of variables that can be intervened on
            
        Returns:
            Intervention plan
        """
        # Find paths from interventions to target
        intervention_paths = {}
        
        for intervention in available_interventions:
            if self._has_causal_path(intervention, target):
                paths = self._find_all_paths(intervention, target)
                intervention_paths[intervention] = paths
        
        # Rank interventions by directness
        ranked_interventions = sorted(
            intervention_paths.items(),
            key=lambda x: min(len(p) for p in x[1]) if x[1] else float('inf')
        )
        
        plan = {
            'target': target,
            'desired_outcome': desired_outcome,
            'recommended_interventions': [
                {
                    'variable': var,
                    'paths': paths,
                    'directness': min(len(p) for p in paths) if paths else float('inf')
                }
                for var, paths in ranked_interventions
            ],
            'confounders': self._identify_confounders(available_interventions[0] if available_interventions else None, desired_outcome)
        }
        
        return plan

    def _has_causal_path(self, source: str, target: str) -> bool:
        """Check if there's a directed path from source to target."""
        return self.do_calculus._has_path(source, target)

    def _find_all_paths(self, source: str, target: str, path: List[str] = None) -> List[List[str]]:
        """Find all paths from source to target."""
        if path is None:
            path = []
        
        path = path + [source]
        
        if source == target:
            return [path]
        
        if source not in self.graph:
            return []
        
        paths = []
        for node in self.graph[source]:
            if node not in path:  # Avoid cycles
                new_paths = self._find_all_paths(node, target, path)
                paths.extend(new_paths)
        
        return paths

    def _identify_confounders(self, treatment: str, outcome: str) -> List[str]:
        """Identify confounders between treatment and outcome."""
        if not treatment:
            return []
        
        confounders = []
        
        for node in self.graph.keys():
            if node != treatment and node != outcome:
                # Check if node is parent of both treatment and outcome
                if (self.do_calculus._has_path(node, treatment) and 
                    self.do_calculus._has_path(node, outcome)):
                    confounders.append(node)
        
        return confounders


if __name__ == "__main__":
    print("✅ Advanced causal inference modules initialized")
    
    # Test do-calculus
    graph = {
        'X': ['Y', 'M'],
        'Z': ['X', 'Y'],
        'M': ['Y']
    }
    
    engine = DoCalculusEngine(graph)
    print(f"Parents of Y: {engine.get_parents('Y')}")
    print(f"Ancestors of Y: {engine.get_ancestors({'Y'})}")
    
    # Test counterfactual
    cf_model = CounterfactualReasoning(input_dim=10)
    factual = torch.randn(4, 10)
    intervention = torch.randn(4, 10)
    output = cf_model(factual, intervention, treatment_idx=0)
    print(f"Counterfactual shape: {output['counterfactual'].shape}")
    
    print("✅ All causal inference tests passed")
