"""
Model-Agnostic Meta-Learning (MAML) for Few-Shot Causal Discovery.

Enables rapid adaptation to new scientific domains with minimal data.
Based on: "Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks" (Finn et al., ICML 2017)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
from collections import OrderedDict
import copy


class MAML(nn.Module):
    """
    Model-Agnostic Meta-Learning implementation.
    
    Learns an initialization that can quickly adapt to new tasks with few examples.
    """
    
    def __init__(
        self,
        model: nn.Module,
        inner_lr: float = 0.01,
        outer_lr: float = 0.001,
        inner_steps: int = 5,
        first_order: bool = False
    ):
        """
        Initialize MAML.
        
        Args:
            model: Base model to meta-learn
            inner_lr: Learning rate for inner loop (task adaptation)
            outer_lr: Learning rate for outer loop (meta-update)
            inner_steps: Number of gradient steps in inner loop
            first_order: Use first-order approximation (faster but less accurate)
        """
        super().__init__()
        self.model = model
        self.inner_lr = inner_lr
        self.outer_lr = outer_lr
        self.inner_steps = inner_steps
        self.first_order = first_order
        
        # Meta optimizer
        self.meta_optimizer = torch.optim.Adam(self.model.parameters(), lr=outer_lr)
    
    def inner_loop(
        self,
        support_batch: Dict[str, torch.Tensor],
        fast_weights: Optional[OrderedDict] = None
    ) -> OrderedDict:
        """
        Perform inner loop adaptation on support set.
        
        Args:
            support_batch: Support set batch (few-shot examples)
            fast_weights: Current fast weights (if None, use model weights)
            
        Returns:
            Adapted fast weights
        """
        if fast_weights is None:
            fast_weights = OrderedDict(self.model.named_parameters())
        
        # Perform K gradient steps
        for step in range(self.inner_steps):
            # Forward pass with fast weights
            logits = self._forward_with_weights(support_batch, fast_weights)
            
            # Compute loss
            loss = F.cross_entropy(logits, support_batch['labels'])
            
            # Compute gradients
            grads = torch.autograd.grad(
                loss,
                fast_weights.values(),
                create_graph=not self.first_order,
                allow_unused=True
            )
            
            # Update fast weights
            fast_weights = OrderedDict(
                (name, param - self.inner_lr * grad if grad is not None else param)
                for ((name, param), grad) in zip(fast_weights.items(), grads)
            )
        
        return fast_weights
    
    def _forward_with_weights(
        self,
        batch: Dict[str, torch.Tensor],
        weights: OrderedDict
    ) -> torch.Tensor:
        """Forward pass using custom weights."""
        # This is a simplified version - adapt based on your model structure
        x = batch['input_ids']
        
        # Manually apply weights
        # Note: This needs to be customized for your specific model architecture
        return self._functional_forward(x, weights)
    
    def _functional_forward(self, x: torch.Tensor, weights: OrderedDict) -> torch.Tensor:
        """
        Functional forward pass.
        
        This should be implemented based on your specific model architecture.
        """
        # Example implementation for a simple model
        # You'll need to adapt this for transformer-based models
        
        for name, param in weights.items():
            if 'weight' in name and 'layer' in name:
                x = F.linear(x, param, weights.get(name.replace('weight', 'bias')))
                x = F.relu(x)
        
        return x
    
    def meta_train_step(
        self,
        task_batch: List[Tuple[Dict, Dict]]
    ) -> Dict[str, float]:
        """
        Perform one meta-training step across multiple tasks.
        
        Args:
            task_batch: List of (support_batch, query_batch) tuples
            
        Returns:
            Dictionary of metrics
        """
        self.meta_optimizer.zero_grad()
        
        meta_loss = 0.0
        meta_accuracy = 0.0
        
        for support_batch, query_batch in task_batch:
            # Inner loop: adapt to support set
            fast_weights = self.inner_loop(support_batch)
            
            # Outer loop: evaluate on query set
            query_logits = self._forward_with_weights(query_batch, fast_weights)
            query_loss = F.cross_entropy(query_logits, query_batch['labels'])
            
            # Accumulate meta loss
            meta_loss += query_loss
            
            # Compute accuracy
            query_preds = torch.argmax(query_logits, dim=-1)
            accuracy = (query_preds == query_batch['labels']).float().mean()
            meta_accuracy += accuracy
        
        # Average over tasks
        meta_loss = meta_loss / len(task_batch)
        meta_accuracy = meta_accuracy / len(task_batch)
        
        # Meta backward pass
        meta_loss.backward()
        
        # Meta optimization step
        self.meta_optimizer.step()
        
        return {
            'meta_loss': meta_loss.item(),
            'meta_accuracy': meta_accuracy.item()
        }
    
    def adapt(
        self,
        support_batch: Dict[str, torch.Tensor],
        num_steps: Optional[int] = None
    ) -> nn.Module:
        """
        Adapt model to new task using support set.
        
        Args:
            support_batch: Support set for adaptation
            num_steps: Number of adaptation steps (if None, use default)
            
        Returns:
            Adapted model
        """
        if num_steps is not None:
            original_steps = self.inner_steps
            self.inner_steps = num_steps
        
        # Perform adaptation
        fast_weights = self.inner_loop(support_batch)
        
        # Create adapted model
        adapted_model = copy.deepcopy(self.model)
        adapted_model.load_state_dict(fast_weights, strict=False)
        
        if num_steps is not None:
            self.inner_steps = original_steps
        
        return adapted_model


class PrototypicalNetwork(nn.Module):
    """
    Prototypical Networks for few-shot learning.
    
    Learns a metric space where classification is based on distance to class prototypes.
    Simpler alternative to MAML, often works well for classification tasks.
    """
    
    def __init__(self, encoder: nn.Module, distance_metric: str = 'euclidean'):
        """
        Initialize Prototypical Network.
        
        Args:
            encoder: Neural network to encode inputs
            distance_metric: 'euclidean' or 'cosine'
        """
        super().__init__()
        self.encoder = encoder
        self.distance_metric = distance_metric
    
    def compute_prototypes(
        self,
        support_embeddings: torch.Tensor,
        support_labels: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute class prototypes as mean of support embeddings.
        
        Args:
            support_embeddings: [N, D] embeddings
            support_labels: [N] labels
            
        Returns:
            [K, D] prototypes for K classes
        """
        classes = torch.unique(support_labels)
        prototypes = []
        
        for c in classes:
            mask = support_labels == c
            class_embeddings = support_embeddings[mask]
            prototype = class_embeddings.mean(dim=0)
            prototypes.append(prototype)
        
        return torch.stack(prototypes)
    
    def compute_distances(
        self,
        query_embeddings: torch.Tensor,
        prototypes: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute distances from queries to prototypes.
        
        Args:
            query_embeddings: [M, D] query embeddings
            prototypes: [K, D] class prototypes
            
        Returns:
            [M, K] distance matrix
        """
        if self.distance_metric == 'euclidean':
            # Euclidean distance
            distances = torch.cdist(query_embeddings, prototypes, p=2)
        elif self.distance_metric == 'cosine':
            # Cosine similarity (negative for distance)
            query_norm = F.normalize(query_embeddings, p=2, dim=1)
            proto_norm = F.normalize(prototypes, p=2, dim=1)
            distances = -torch.matmul(query_norm, proto_norm.T)
        else:
            raise ValueError(f"Unknown distance metric: {self.distance_metric}")
        
        return distances
    
    def forward(
        self,
        support_inputs: Dict[str, torch.Tensor],
        support_labels: torch.Tensor,
        query_inputs: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        Forward pass for few-shot episode.
        
        Args:
            support_inputs: Support set inputs
            support_labels: Support set labels
            query_inputs: Query set inputs
            
        Returns:
            Query logits [M, K]
        """
        # Encode support and query sets
        support_embeddings = self.encoder(**support_inputs)
        query_embeddings = self.encoder(**query_inputs)
        
        # Handle dict outputs
        if isinstance(support_embeddings, dict):
            support_embeddings = support_embeddings['embeddings']
        if isinstance(query_embeddings, dict):
            query_embeddings = query_embeddings['embeddings']
        
        # Compute prototypes
        prototypes = self.compute_prototypes(support_embeddings, support_labels)
        
        # Compute distances (negative for logits)
        distances = self.compute_distances(query_embeddings, prototypes)
        logits = -distances
        
        return logits


class RelationNetwork(nn.Module):
    """
    Relation Networks for few-shot learning.
    
    Learns a relation module to compare query and support examples.
    More flexible than prototypical networks.
    """
    
    def __init__(self, encoder: nn.Module, hidden_dim: int = 128):
        """
        Initialize Relation Network.
        
        Args:
            encoder: Neural network to encode inputs
            hidden_dim: Hidden dimension for relation module
        """
        super().__init__()
        self.encoder = encoder
        
        # Relation module (learns similarity metric)
        self.relation_module = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        support_inputs: Dict[str, torch.Tensor],
        support_labels: torch.Tensor,
        query_inputs: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        Forward pass for few-shot episode.
        
        Args:
            support_inputs: Support set inputs
            support_labels: Support set labels
            query_inputs: Query set inputs
            
        Returns:
            Relation scores [M, N]
        """
        # Encode
        support_embeddings = self.encoder(**support_inputs)
        query_embeddings = self.encoder(**query_inputs)
        
        # Handle dict outputs
        if isinstance(support_embeddings, dict):
            support_embeddings = support_embeddings['embeddings']
        if isinstance(query_embeddings, dict):
            query_embeddings = query_embeddings['embeddings']
        
        # Compute pairwise relations
        M = query_embeddings.shape[0]
        N = support_embeddings.shape[0]
        
        relation_scores = []
        
        for i in range(M):
            query_repeated = query_embeddings[i].unsqueeze(0).repeat(N, 1)
            pairs = torch.cat([query_repeated, support_embeddings], dim=1)
            scores = self.relation_module(pairs)
            relation_scores.append(scores)
        
        relation_scores = torch.cat(relation_scores, dim=1).T  # [M, N]
        
        return relation_scores


def create_episode(
    dataset: List[Dict],
    n_way: int = 5,
    k_shot: int = 5,
    q_query: int = 15
) -> Tuple[Dict, Dict]:
    """
    Create a few-shot learning episode.
    
    Args:
        dataset: List of examples with 'inputs' and 'label'
        n_way: Number of classes per episode
        k_shot: Number of support examples per class
        q_query: Number of query examples per class
        
    Returns:
        Tuple of (support_batch, query_batch)
    """
    import random
    
    # Group by class
    class_examples = {}
    for example in dataset:
        label = example['label']
        if label not in class_examples:
            class_examples[label] = []
        class_examples[label].append(example)
    
    # Sample n_way classes
    sampled_classes = random.sample(list(class_examples.keys()), n_way)
    
    support_examples = []
    query_examples = []
    
    for new_label, original_class in enumerate(sampled_classes):
        examples = class_examples[original_class]
        sampled = random.sample(examples, k_shot + q_query)
        
        # Support set
        for ex in sampled[:k_shot]:
            support_examples.append({
                **ex['inputs'],
                'label': new_label
            })
        
        # Query set
        for ex in sampled[k_shot:]:
            query_examples.append({
                **ex['inputs'],
                'label': new_label
            })
    
    # Batch
    support_batch = collate_examples(support_examples)
    query_batch = collate_examples(query_examples)
    
    return support_batch, query_batch


def collate_examples(examples: List[Dict]) -> Dict[str, torch.Tensor]:
    """Collate examples into batch."""
    batch = {}
    
    for key in examples[0].keys():
        if isinstance(examples[0][key], torch.Tensor):
            batch[key] = torch.stack([ex[key] for ex in examples])
        else:
            batch[key] = torch.tensor([ex[key] for ex in examples])
    
    return batch


if __name__ == "__main__":
    print("✅ Meta-learning modules initialized")
    
    # Test prototypical network
    from torch import nn as nn_module
    
    encoder = nn_module.Sequential(
        nn_module.Linear(128, 256),
        nn_module.ReLU(),
        nn_module.Linear(256, 128)
    )
    
    proto_net = PrototypicalNetwork(encoder)
    print("✅ Prototypical Network created")
    
    relation_net = RelationNetwork(encoder)
    print("✅ Relation Network created")
    
    print("Meta-learning ready for few-shot causal discovery!")
