"""Graph Neural Network models for causal learning."""

import torch
import torch.nn as nn
from typing import Tuple, List, Dict

class DAGLearner(nn.Module):
    """Differentiable DAG learner with attention."""

    def __init__(self, num_nodes: int, hidden_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim

        # Attention mechanism for DAG structure
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=4, dropout=dropout, batch_first=True)
        self.fc1 = nn.Linear(hidden_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 1)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Learn DAG structure.
        
        Args:
            embeddings: Tensor of shape [N, hidden_dim] or [B, N, hidden_dim]
            
        Returns:
            Tuple of (adjacency, loss_acyclic)
        """
        # Handle batch dimension if present
        if embeddings.dim() == 3:
            embeddings = embeddings.squeeze(0)  # [B, N, C] -> [N, C]
            
        # Self-attention
        attn_out, _ = self.attention(embeddings.unsqueeze(0), embeddings.unsqueeze(0), embeddings.unsqueeze(0))
        attn_out = attn_out.squeeze(0)
        attn_out = self.dropout(attn_out)

        # Score edges
        edge_logits = self.fc2(self.relu(self.fc1(attn_out)))
        adjacency = torch.sigmoid(edge_logits).squeeze(-1)

        # Enforce acyclicity constraint
        A = adjacency
        h = torch.trace(torch.matrix_power(torch.eye(self.num_nodes, device=A.device) + A / self.num_nodes, self.num_nodes))
        loss_acyclic = h + 1  # Should be close to 1 for DAG

        return adjacency, loss_acyclic


class GraphAttentionNetwork(nn.Module):
    """Graph Attention Network for causal reasoning."""

    def __init__(self, input_dim: int, hidden_dim: int = 128, num_layers: int = 3, dropout: float = 0.1):
        super().__init__()
        self.layers = nn.ModuleList()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        for i in range(num_layers):
            in_dim = input_dim if i == 0 else hidden_dim
            self.layers.append(GATLayer(in_dim, hidden_dim, dropout))

        self.output_layer = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, node_features: torch.Tensor, adjacency: torch.Tensor) -> torch.Tensor:
        """Forward pass through GAT."""
        x = node_features
        for layer in self.layers:
            x = layer(x, adjacency)
        x = self.output_layer(x)
        return x


class GATLayer(nn.Module):
    """Single Graph Attention layer."""

    def __init__(self, input_dim: int, output_dim: int, dropout: float = 0.1, num_heads: int = 4):
        super().__init__()
        self.num_heads = num_heads
        self.output_dim = output_dim
        self.head_dim = output_dim // num_heads

        assert output_dim % num_heads == 0, "output_dim must be divisible by num_heads"

        self.linear = nn.Linear(input_dim, output_dim)
        self.attention_linear = nn.Linear(output_dim, 1)  # Changed: take output_dim, not 2*head_dim
        self.dropout = nn.Dropout(dropout)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        B, N, C = x.shape
        x_proj = self.linear(x)  # [B, N, output_dim]

        # Simplified attention: compute score for each node
        scores = self.attention_linear(x_proj)  # [B, N, 1]
        scores = scores.squeeze(-1)  # [B, N]
        scores = self.leaky_relu(scores)

        # Expand to [B, N, N] for matrix multiplication
        scores = scores.unsqueeze(1).expand(-1, N, -1)  # [B, N, N]
        
        # Mask and normalize
        if adj.dim() == 2:
            mask = (adj > 0).unsqueeze(0)  # [1, N, N]
        else:
            mask = (adj > 0)
        
        mask = mask.expand_as(scores)
        scores = torch.where(mask, scores, torch.tensor(float('-inf'), device=scores.device))
        attention_weights = torch.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)

        # Apply attention
        output = torch.matmul(attention_weights, x_proj)  # [B, N, output_dim]

        return output


class CausalGraphModel(nn.Module):
    """Complete causal graph learning model."""

    def __init__(self, num_nodes: int, input_dim: int = 128, hidden_dim: int = 128):
        super().__init__()
        self.dag_learner = DAGLearner(num_nodes, hidden_dim)
        self.gat = GraphAttentionNetwork(input_dim, hidden_dim)
        self.consistency_scorer = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, embeddings: torch.Tensor, edge_features: torch.Tensor) -> Dict:
        """Forward pass.
        
        Args:
            embeddings: Node embeddings [B, N, C] or [N, C]
            edge_features: Edge features [B, N, N] or [N, N]
            
        Returns:
            Dictionary with adjacency, node_embeddings, consistency_scores, acyclic_loss
        """
        # Learn DAG structure (DAGLearner handles batch dimension internally)
        adjacency, acyclic_loss = self.dag_learner(embeddings)

        # Get node representations
        node_reprs = self.gat(embeddings, adjacency)

        # Score consistency for each edge
        consistency_scores = []
        
        # Handle both 2D [N, N] and 3D [B, N, N] adjacency
        if adjacency.dim() == 2:
            num_nodes = adjacency.shape[0]
            for i in range(num_nodes):
                for j in range(num_nodes):
                    if adjacency[i, j] > 0.5:
                        # Handle node_reprs dimensions
                        if node_reprs.dim() == 3:
                            edge_feat = torch.cat([node_reprs[0, i], node_reprs[0, j]], dim=-1)
                        else:
                            edge_feat = torch.cat([node_reprs[i], node_reprs[j]], dim=-1)
                        score = self.consistency_scorer(edge_feat)
                        consistency_scores.append(score)

        return {
            "adjacency": adjacency,
            "node_embeddings": node_reprs,
            "consistency_scores": consistency_scores,
            "acyclic_loss": acyclic_loss
        }


if __name__ == "__main__":
    model = CausalGraphModel(num_nodes=10, input_dim=128, hidden_dim=128)
    embeddings = torch.randn(1, 10, 128)
    edge_features = torch.randn(1, 10, 10)
    output = model(embeddings, edge_features)
    print("✅ Model initialized")
    print(f"Adjacency shape: {output['adjacency'].shape}")
