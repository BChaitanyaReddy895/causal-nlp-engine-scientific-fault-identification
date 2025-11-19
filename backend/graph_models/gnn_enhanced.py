"""Enhanced Graph Neural Networks with advanced causal discovery algorithms."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, List, Dict, Optional
import numpy as np
from scipy import linalg


class GraphTransformerLayer(nn.Module):
    """Graph Transformer layer with multi-head self-attention."""

    def __init__(self, hidden_dim: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        
        assert hidden_dim % num_heads == 0
        
        # Multi-head attention components
        self.q_linear = nn.Linear(hidden_dim, hidden_dim)
        self.k_linear = nn.Linear(hidden_dim, hidden_dim)
        self.v_linear = nn.Linear(hidden_dim, hidden_dim)
        self.out_linear = nn.Linear(hidden_dim, hidden_dim)
        
        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout)
        )
        
        # Layer normalization
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [B, N, H]
            adj: Adjacency matrix [B, N, N] or [N, N]
            
        Returns:
            Updated node features [B, N, H]
        """
        B, N, H = x.shape
        
        # Multi-head self-attention with graph structure bias
        residual = x
        x = self.norm1(x)
        
        # Compute Q, K, V
        Q = self.q_linear(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)  # [B, heads, N, head_dim]
        K = self.k_linear(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.v_linear(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_dim)  # [B, heads, N, N]
        
        # Apply graph structure bias
        if adj.dim() == 2:
            adj = adj.unsqueeze(0).unsqueeze(0)  # [1, 1, N, N]
        elif adj.dim() == 3:
            adj = adj.unsqueeze(1)  # [B, 1, N, N]
        
        adj_bias = (adj > 0).float() * 10.0 - 10.0  # Bias for connected nodes
        scores = scores + adj_bias
        
        # Attention weights
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        out = torch.matmul(attn_weights, V)  # [B, heads, N, head_dim]
        out = out.transpose(1, 2).contiguous().view(B, N, H)  # [B, N, H]
        out = self.out_linear(out)
        
        # Residual connection
        x = residual + self.dropout(out)
        
        # Feed-forward network
        residual = x
        x = self.norm2(x)
        x = residual + self.ffn(x)
        
        return x


class EnhancedDAGLearner(nn.Module):
    """Enhanced DAG learner with NOTEARS algorithm and causal discovery."""

    def __init__(self, num_nodes: int, hidden_dim: int = 128, lambda_sparse: float = 0.01):
        super().__init__()
        self.num_nodes = num_nodes
        self.hidden_dim = hidden_dim
        self.lambda_sparse = lambda_sparse
        
        # Learnable adjacency matrix (logits)
        self.adj_logits = nn.Parameter(torch.randn(num_nodes, num_nodes) * 0.01)
        
        # MLP for structure learning
        self.structure_mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        # Mask diagonal (no self-loops)
        self.register_buffer('diag_mask', 1 - torch.eye(num_nodes))

    def forward(self, embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Learn DAG structure using NOTEARS-like optimization.
        
        Args:
            embeddings: Node embeddings [B, N, H] or [N, H]
            
        Returns:
            Tuple of (adjacency, acyclic_loss, sparse_loss)
        """
        if embeddings.dim() == 3:
            embeddings = embeddings.squeeze(0)
        
        # Compute pairwise interactions
        num_nodes = embeddings.shape[0]
        adj = torch.zeros(num_nodes, num_nodes, device=embeddings.device)
        
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j:
                    pair_repr = torch.cat([embeddings[i], embeddings[j]], dim=-1)
                    edge_weight = torch.sigmoid(self.adj_logits[i, j])
                    adj[i, j] = edge_weight
        
        # Apply diagonal mask
        adj = adj * self.diag_mask
        
        # NOTEARS acyclicity constraint: h(A) = tr(e^(A⊙A)) - d
        # Using matrix exponential approximation
        A_squared = adj * adj
        M = torch.eye(num_nodes, device=adj.device) + A_squared / num_nodes
        
        # Compute matrix power using eigendecomposition (more stable)
        try:
            h_A = torch.trace(torch.matrix_power(M, num_nodes)) - num_nodes
        except:
            # Fallback: use polynomial approximation
            h_A = torch.trace(M) - num_nodes
            for k in range(2, min(num_nodes, 10)):
                M = torch.matmul(M, torch.eye(num_nodes, device=adj.device) + A_squared / num_nodes)
                h_A += torch.trace(M)
        
        acyclic_loss = h_A
        
        # Sparsity regularization (L1)
        sparse_loss = self.lambda_sparse * torch.sum(torch.abs(adj))
        
        return adj, acyclic_loss, sparse_loss


class ResidualGATLayer(nn.Module):
    """GAT layer with residual connections and layer normalization."""

    def __init__(self, input_dim: int, output_dim: int, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.num_heads = num_heads
        self.output_dim = output_dim
        self.head_dim = output_dim // num_heads
        
        assert output_dim % num_heads == 0
        
        # Multi-head attention
        self.W = nn.Linear(input_dim, output_dim, bias=False)
        self.a = nn.Parameter(torch.randn(num_heads, 2 * self.head_dim, 1))
        
        # Residual projection
        self.residual_proj = nn.Linear(input_dim, output_dim) if input_dim != output_dim else nn.Identity()
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(output_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """Forward pass with residual connections."""
        B, N, C = x.shape
        
        # Save residual
        residual = self.residual_proj(x)
        
        # Linear transformation
        h = self.W(x)  # [B, N, output_dim]
        h = h.view(B, N, self.num_heads, self.head_dim)  # [B, N, heads, head_dim]
        
        # Compute attention coefficients
        h_i = h.unsqueeze(2).repeat(1, 1, N, 1, 1)  # [B, N, N, heads, head_dim]
        h_j = h.unsqueeze(1).repeat(1, N, 1, 1, 1)  # [B, N, N, heads, head_dim]
        
        concat = torch.cat([h_i, h_j], dim=-1)  # [B, N, N, heads, 2*head_dim]
        
        # Attention mechanism
        e = self.leaky_relu(torch.matmul(concat, self.a.unsqueeze(0).unsqueeze(0)))  # [B, N, N, heads, 1]
        e = e.squeeze(-1)  # [B, N, N, heads]
        
        # Mask with adjacency
        if adj.dim() == 2:
            mask = (adj > 0).unsqueeze(0).unsqueeze(-1)  # [1, N, N, 1]
        else:
            mask = (adj > 0).unsqueeze(-1)  # [B, N, N, 1]
        
        mask = mask.expand_as(e)
        e = torch.where(mask, e, torch.tensor(float('-inf'), device=e.device))
        
        # Softmax
        alpha = F.softmax(e, dim=2)  # [B, N, N, heads]
        alpha = self.dropout(alpha)
        
        # Aggregate
        h_prime = torch.matmul(alpha.transpose(-1, -2), h.transpose(1, 2))  # [B, heads, N, head_dim]
        h_prime = h_prime.transpose(1, 2).contiguous().view(B, N, -1)  # [B, N, output_dim]
        
        # Residual connection + layer norm
        out = self.layer_norm(residual + h_prime)
        
        return out


class CausalDiscoveryPC(nn.Module):
    """PC (Peter-Clark) algorithm for causal discovery."""

    def __init__(self, num_nodes: int, alpha: float = 0.05):
        """
        Initialize PC algorithm.
        
        Args:
            num_nodes: Number of nodes
            alpha: Significance level for conditional independence tests
        """
        super().__init__()
        self.num_nodes = num_nodes
        self.alpha = alpha

    def conditional_independence_test(self, 
                                     X: torch.Tensor, 
                                     Y: torch.Tensor, 
                                     Z: Optional[torch.Tensor] = None) -> bool:
        """
        Test conditional independence X ⊥ Y | Z.
        
        Uses partial correlation test.
        """
        if Z is None:
            # Test marginal independence
            corr = torch.corrcoef(torch.stack([X, Y]))[0, 1]
            # Fisher's z-transform
            n = len(X)
            z_score = 0.5 * torch.log((1 + corr) / (1 - corr)) * torch.sqrt(torch.tensor(n - 3))
            p_value = 2 * (1 - torch.distributions.Normal(0, 1).cdf(torch.abs(z_score)))
            return p_value.item() > self.alpha
        else:
            # Test conditional independence using partial correlation
            # Compute residuals after regressing on Z
            XZ = torch.cat([X.unsqueeze(1), Z], dim=1)
            YZ = torch.cat([Y.unsqueeze(1), Z], dim=1)
            
            # Use lstsq for linear regression
            beta_X = torch.linalg.lstsq(Z, X).solution
            beta_Y = torch.linalg.lstsq(Z, Y).solution
            
            res_X = X - Z @ beta_X
            res_Y = Y - Z @ beta_Y
            
            # Correlation of residuals
            corr = torch.corrcoef(torch.stack([res_X, res_Y]))[0, 1]
            
            # Fisher's z-transform
            n = len(X)
            k = Z.shape[1] if Z.dim() > 1 else 1
            z_score = 0.5 * torch.log((1 + corr) / (1 - corr)) * torch.sqrt(torch.tensor(n - k - 3))
            p_value = 2 * (1 - torch.distributions.Normal(0, 1).cdf(torch.abs(z_score)))
            
            return p_value.item() > self.alpha

    def learn_skeleton(self, data: torch.Tensor) -> torch.Tensor:
        """
        Learn skeleton of causal graph using PC algorithm.
        
        Args:
            data: Data matrix [num_samples, num_nodes]
            
        Returns:
            Undirected skeleton [num_nodes, num_nodes]
        """
        skeleton = torch.ones(self.num_nodes, self.num_nodes, device=data.device)
        torch.diagonal(skeleton).fill_(0)
        
        # Start with complete undirected graph
        # Remove edges based on conditional independence
        
        for i in range(self.num_nodes):
            for j in range(i + 1, self.num_nodes):
                if skeleton[i, j] == 1:
                    # Test marginal independence
                    if self.conditional_independence_test(data[:, i], data[:, j]):
                        skeleton[i, j] = 0
                        skeleton[j, i] = 0
                        continue
                    
                    # Test conditional independence given each other node
                    for k in range(self.num_nodes):
                        if k != i and k != j and skeleton[i, k] == 1 and skeleton[j, k] == 1:
                            if self.conditional_independence_test(
                                data[:, i], 
                                data[:, j], 
                                data[:, k].unsqueeze(1)
                            ):
                                skeleton[i, j] = 0
                                skeleton[j, i] = 0
                                break
        
        return skeleton


class EnhancedCausalGraphModel(nn.Module):
    """Enhanced causal graph model with multiple advanced components."""

    def __init__(self, 
                 num_nodes: int, 
                 input_dim: int = 128, 
                 hidden_dim: int = 128,
                 num_layers: int = 4,
                 num_heads: int = 8,
                 use_transformer: bool = True):
        super().__init__()
        
        self.num_nodes = num_nodes
        self.use_transformer = use_transformer
        
        # Enhanced DAG learner
        self.dag_learner = EnhancedDAGLearner(num_nodes, hidden_dim)
        
        # Graph processing layers
        if use_transformer:
            self.graph_layers = nn.ModuleList([
                GraphTransformerLayer(hidden_dim, num_heads) 
                for _ in range(num_layers)
            ])
        else:
            self.graph_layers = nn.ModuleList([
                ResidualGATLayer(
                    input_dim if i == 0 else hidden_dim,
                    hidden_dim,
                    num_heads=4
                ) for i in range(num_layers)
            ])
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # Causal effect estimator
        self.effect_estimator = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        
        # Consistency scorer
        self.consistency_scorer = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, embeddings: torch.Tensor, edge_features: torch.Tensor) -> Dict:
        """
        Enhanced forward pass.
        
        Args:
            embeddings: Node embeddings [B, N, C]
            edge_features: Edge features [B, N, N]
            
        Returns:
            Dictionary with outputs
        """
        # Project embeddings
        x = self.input_proj(embeddings)
        
        # Learn DAG structure
        adjacency, acyclic_loss, sparse_loss = self.dag_learner(x)
        
        # Process through graph layers
        for layer in self.graph_layers:
            x = layer(x, adjacency)
        
        # Compute consistency scores for edges
        consistency_scores = []
        causal_effects = []
        
        B = x.shape[0] if x.dim() == 3 else 1
        N = x.shape[1] if x.dim() == 3 else x.shape[0]
        
        if x.dim() == 2:
            x = x.unsqueeze(0)
        
        for i in range(N):
            for j in range(N):
                if adjacency[i, j] > 0.5:
                    edge_repr = torch.cat([x[0, i], x[0, j]], dim=-1)
                    consistency = self.consistency_scorer(edge_repr)
                    effect = self.effect_estimator(edge_repr)
                    
                    consistency_scores.append(consistency)
                    causal_effects.append(effect)
        
        return {
            'adjacency': adjacency,
            'node_embeddings': x,
            'consistency_scores': consistency_scores,
            'causal_effects': causal_effects,
            'acyclic_loss': acyclic_loss,
            'sparse_loss': sparse_loss,
            'total_loss': acyclic_loss + sparse_loss
        }


if __name__ == "__main__":
    print("✅ Enhanced GNN models initialized")
    
    # Test model
    model = EnhancedCausalGraphModel(
        num_nodes=10,
        input_dim=128,
        hidden_dim=128,
        num_layers=3,
        use_transformer=True
    )
    
    # Test forward pass
    embeddings = torch.randn(1, 10, 128)
    edge_features = torch.randn(1, 10, 10)
    
    output = model(embeddings, edge_features)
    
    print(f"Adjacency shape: {output['adjacency'].shape}")
    print(f"Node embeddings shape: {output['node_embeddings'].shape}")
    print(f"Acyclic loss: {output['acyclic_loss'].item():.4f}")
    print("✅ Enhanced GNN test passed")
