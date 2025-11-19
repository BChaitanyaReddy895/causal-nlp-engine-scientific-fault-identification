"""Training script for graph models."""

import torch
import torch.optim as optim
from pathlib import Path
import json

class TrainingPipeline:
    """Training pipeline for graph models."""

    def __init__(self, model, learning_rate: float = 0.001, num_epochs: int = 100):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.num_epochs = num_epochs
        self.losses = []

    def train_epoch(self, data_loader, device='cpu'):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0

        for batch_idx, (embeddings, edge_features, labels) in enumerate(data_loader):
            embeddings = embeddings.to(device)
            edge_features = edge_features.to(device)
            labels = labels.to(device)

            self.optimizer.zero_grad()

            # Forward pass
            output = self.model(embeddings, edge_features)

            # Compute loss
            acyclic_loss = output['acyclic_loss'].mean() if isinstance(output['acyclic_loss'], torch.Tensor) else torch.tensor(output['acyclic_loss'], device=device)
            consistency_loss = torch.tensor(0.0, device=device)

            if output['consistency_scores'] and len(output['consistency_scores']) > 0:
                consistency_scores = torch.stack(output['consistency_scores']).mean()
                consistency_loss = torch.abs(1.0 - consistency_scores)

            loss = acyclic_loss + consistency_loss
            total_loss += loss.item()

            # Backward pass
            loss.backward()
            self.optimizer.step()

        avg_loss = total_loss / (batch_idx + 1) if batch_idx >= 0 else 0
        self.losses.append(avg_loss)
        return avg_loss

    def train(self, data_loader, device='cpu'):
        """Full training loop."""
        for epoch in range(self.num_epochs):
            loss = self.train_epoch(data_loader, device)
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{self.num_epochs}, Loss: {loss:.4f}")

        print(f"✅ Training complete. Final loss: {self.losses[-1]:.4f}")

    def save_checkpoint(self, path: str):
        """Save model checkpoint."""
        torch.save({
            'model_state': self.model.state_dict(),
            'losses': self.losses
        }, path)
        print(f"✅ Checkpoint saved to {path}")


def create_dummy_dataloader(num_samples: int = 32, num_nodes: int = 10):
    """Create dummy data loader for testing."""
    data = []
    for _ in range(num_samples):
        embeddings = torch.randn(1, num_nodes, 128)
        edge_features = torch.randn(1, num_nodes, num_nodes)
        labels = torch.randn(num_nodes, num_nodes)
        data.append((embeddings, edge_features, labels))
    return data


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from backend.graph_models.gnn import CausalGraphModel

    print("Initializing training pipeline...")
    model = CausalGraphModel(num_nodes=10)
    pipeline = TrainingPipeline(model, num_epochs=20)

    # Create dummy data
    data = create_dummy_dataloader(num_samples=4)

    # Train
    pipeline.train(data)

    # Save
    pipeline.save_checkpoint("models/graph_model/causal_graph_model.pt")
