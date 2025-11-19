"""
Advanced Training Infrastructure for Production-Grade Model Training.

Features:
- Distributed Data Parallel (DDP) training
- Mixed Precision Training (AMP)
- Advanced learning rate scheduling
- Gradient accumulation
- Model checkpointing with best model tracking
- Early stopping with patience
- Comprehensive logging and metrics
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, DistributedSampler
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.cuda.amp import autocast, GradScaler
import torch.distributed as dist
from typing import Dict, List, Optional, Callable, Tuple
from pathlib import Path
import json
import numpy as np
from collections import defaultdict
import time
from datetime import datetime


class AdvancedTrainer:
    """Production-grade trainer with all modern techniques."""
    
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        criterion: nn.Module,
        optimizer: optim.Optimizer,
        device: torch.device,
        config: Dict,
        checkpoint_dir: str = "checkpoints",
        use_amp: bool = True,
        use_ddp: bool = False,
        rank: int = 0,
        world_size: int = 1
    ):
        """
        Initialize advanced trainer.
        
        Args:
            model: PyTorch model
            train_loader: Training data loader
            val_loader: Validation data loader
            criterion: Loss function
            optimizer: Optimizer
            device: Device to train on
            config: Training configuration
            checkpoint_dir: Directory for checkpoints
            use_amp: Use Automatic Mixed Precision
            use_ddp: Use Distributed Data Parallel
            rank: Process rank for DDP
            world_size: Total number of processes
        """
        self.device = device
        self.config = config
        self.use_amp = use_amp
        self.use_ddp = use_ddp
        self.rank = rank
        self.world_size = world_size
        
        # Model setup
        self.model = model.to(device)
        if use_ddp:
            self.model = DDP(model, device_ids=[rank])
        
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.criterion = criterion
        self.optimizer = optimizer
        
        # Mixed precision setup
        self.scaler = GradScaler() if use_amp else None
        
        # Learning rate scheduler
        self.scheduler = self._create_scheduler()
        
        # Checkpointing
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Training state
        self.epoch = 0
        self.global_step = 0
        self.best_val_loss = float('inf')
        self.best_val_metric = 0.0
        self.patience_counter = 0
        
        # Metrics tracking
        self.train_metrics = defaultdict(list)
        self.val_metrics = defaultdict(list)
        
        # Gradient accumulation
        self.gradient_accumulation_steps = config.get('gradient_accumulation_steps', 1)
        
        # Early stopping
        self.early_stopping_patience = config.get('early_stopping_patience', 10)
        self.early_stopping_metric = config.get('early_stopping_metric', 'val_loss')
        
        # Logging
        self.log_interval = config.get('log_interval', 100)
        self.val_interval = config.get('val_interval', 1)  # Validate every N epochs
        
    def _create_scheduler(self):
        """Create learning rate scheduler."""
        scheduler_type = self.config.get('scheduler', 'cosine')
        
        if scheduler_type == 'cosine':
            return optim.lr_scheduler.CosineAnnealingWarmRestarts(
                self.optimizer,
                T_0=self.config.get('T_0', 10),
                T_mult=self.config.get('T_mult', 2),
                eta_min=self.config.get('min_lr', 1e-7)
            )
        elif scheduler_type == 'reduce_on_plateau':
            return optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode='min',
                factor=0.5,
                patience=5,
                verbose=True
            )
        elif scheduler_type == 'one_cycle':
            return optim.lr_scheduler.OneCycleLR(
                self.optimizer,
                max_lr=self.config.get('max_lr', 1e-3),
                epochs=self.config.get('epochs', 100),
                steps_per_epoch=len(self.train_loader),
                pct_start=0.3,
                anneal_strategy='cos'
            )
        else:
            return None
    
    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        epoch_metrics = defaultdict(float)
        num_batches = 0
        
        self.optimizer.zero_grad()
        
        for batch_idx, batch in enumerate(self.train_loader):
            # Move batch to device
            batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                    for k, v in batch.items()}
            
            # Forward pass with mixed precision
            with autocast(enabled=self.use_amp):
                outputs = self.model(**batch)
                loss = self.criterion(outputs, batch)
                
                # Scale loss for gradient accumulation
                loss = loss / self.gradient_accumulation_steps
            
            # Backward pass
            if self.use_amp:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
            
            # Gradient accumulation
            if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                if self.use_amp:
                    # Unscale gradients and clip
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), 
                        self.config.get('max_grad_norm', 1.0)
                    )
                    
                    # Optimizer step
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), 
                        self.config.get('max_grad_norm', 1.0)
                    )
                    self.optimizer.step()
                
                self.optimizer.zero_grad()
                self.global_step += 1
                
                # Update scheduler (if using OneCycleLR)
                if isinstance(self.scheduler, optim.lr_scheduler.OneCycleLR):
                    self.scheduler.step()
            
            # Track metrics
            epoch_metrics['loss'] += loss.item() * self.gradient_accumulation_steps
            
            # Additional metrics from outputs
            if isinstance(outputs, dict):
                for key, value in outputs.items():
                    if 'loss' in key and isinstance(value, torch.Tensor):
                        epoch_metrics[key] += value.item()
            
            num_batches += 1
            
            # Logging
            if batch_idx % self.log_interval == 0 and self.rank == 0:
                current_lr = self.optimizer.param_groups[0]['lr']
                print(f"Epoch [{self.epoch}] Batch [{batch_idx}/{len(self.train_loader)}] "
                      f"Loss: {loss.item() * self.gradient_accumulation_steps:.4f} "
                      f"LR: {current_lr:.2e}")
        
        # Average metrics
        for key in epoch_metrics:
            epoch_metrics[key] /= num_batches
        
        return dict(epoch_metrics)
    
    @torch.no_grad()
    def validate(self) -> Dict[str, float]:
        """Validate on validation set."""
        self.model.eval()
        val_metrics = defaultdict(float)
        num_batches = 0
        
        all_predictions = []
        all_targets = []
        
        for batch in self.val_loader:
            # Move batch to device
            batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                    for k, v in batch.items()}
            
            # Forward pass
            with autocast(enabled=self.use_amp):
                outputs = self.model(**batch)
                loss = self.criterion(outputs, batch)
            
            # Track metrics
            val_metrics['loss'] += loss.item()
            
            # Additional metrics
            if isinstance(outputs, dict):
                for key, value in outputs.items():
                    if 'loss' in key and isinstance(value, torch.Tensor):
                        val_metrics[key] += value.item()
                
                # Collect predictions for metrics
                if 'logits' in outputs:
                    preds = torch.argmax(outputs['logits'], dim=-1)
                    all_predictions.append(preds.cpu())
                    if 'labels' in batch:
                        all_targets.append(batch['labels'].cpu())
            
            num_batches += 1
        
        # Average metrics
        for key in val_metrics:
            val_metrics[key] /= num_batches
        
        # Compute additional metrics
        if all_predictions and all_targets:
            all_predictions = torch.cat(all_predictions)
            all_targets = torch.cat(all_targets)
            
            # Accuracy
            val_metrics['accuracy'] = (all_predictions == all_targets).float().mean().item()
            
            # Per-class metrics
            num_classes = outputs['logits'].shape[-1] if 'logits' in outputs else 2
            for c in range(num_classes):
                mask = all_targets == c
                if mask.sum() > 0:
                    class_acc = (all_predictions[mask] == all_targets[mask]).float().mean().item()
                    val_metrics[f'class_{c}_accuracy'] = class_acc
        
        return dict(val_metrics)
    
    def save_checkpoint(self, is_best: bool = False, extra_info: Dict = None):
        """Save model checkpoint."""
        if self.rank != 0:  # Only save on rank 0
            return
        
        checkpoint = {
            'epoch': self.epoch,
            'global_step': self.global_step,
            'model_state_dict': self.model.module.state_dict() if self.use_ddp else self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_val_loss': self.best_val_loss,
            'best_val_metric': self.best_val_metric,
            'config': self.config
        }
        
        if self.scheduler is not None:
            checkpoint['scheduler_state_dict'] = self.scheduler.state_dict()
        
        if extra_info:
            checkpoint.update(extra_info)
        
        # Save regular checkpoint
        checkpoint_path = self.checkpoint_dir / f"checkpoint_epoch_{self.epoch}.pt"
        torch.save(checkpoint, checkpoint_path)
        
        # Save best checkpoint
        if is_best:
            best_path = self.checkpoint_dir / "best_model.pt"
            torch.save(checkpoint, best_path)
            print(f"✅ Saved best model at epoch {self.epoch}")
        
        # Save latest checkpoint
        latest_path = self.checkpoint_dir / "latest_model.pt"
        torch.save(checkpoint, latest_path)
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        if self.use_ddp:
            self.model.module.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        if 'scheduler_state_dict' in checkpoint and self.scheduler is not None:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        self.epoch = checkpoint['epoch']
        self.global_step = checkpoint['global_step']
        self.best_val_loss = checkpoint['best_val_loss']
        self.best_val_metric = checkpoint.get('best_val_metric', 0.0)
        
        print(f"✅ Loaded checkpoint from epoch {self.epoch}")
    
    def check_early_stopping(self, val_metrics: Dict[str, float]) -> bool:
        """Check if early stopping criteria met."""
        metric_value = val_metrics.get(self.early_stopping_metric, float('inf'))
        
        # Determine if improvement (lower is better for loss, higher for metrics)
        if 'loss' in self.early_stopping_metric:
            improved = metric_value < self.best_val_loss
            if improved:
                self.best_val_loss = metric_value
        else:
            improved = metric_value > self.best_val_metric
            if improved:
                self.best_val_metric = metric_value
        
        if improved:
            self.patience_counter = 0
            return False
        else:
            self.patience_counter += 1
            if self.patience_counter >= self.early_stopping_patience:
                print(f"Early stopping triggered after {self.patience_counter} epochs without improvement")
                return True
        
        return False
    
    def train(self, num_epochs: int):
        """Main training loop."""
        print(f"🚀 Starting training for {num_epochs} epochs")
        print(f"Device: {self.device}")
        print(f"Mixed Precision: {self.use_amp}")
        print(f"Distributed: {self.use_ddp} (Rank {self.rank}/{self.world_size})")
        
        for epoch in range(num_epochs):
            self.epoch = epoch
            
            # Train epoch
            train_metrics = self.train_epoch()
            
            # Store metrics
            for key, value in train_metrics.items():
                self.train_metrics[key].append(value)
            
            # Validation
            if epoch % self.val_interval == 0:
                val_metrics = self.validate()
                
                # Store metrics
                for key, value in val_metrics.items():
                    self.val_metrics[key].append(value)
                
                # Update scheduler
                if isinstance(self.scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                    self.scheduler.step(val_metrics['loss'])
                elif self.scheduler is not None and not isinstance(self.scheduler, optim.lr_scheduler.OneCycleLR):
                    self.scheduler.step()
                
                # Logging
                if self.rank == 0:
                    print(f"\n📊 Epoch [{epoch}/{num_epochs}]")
                    print(f"Train Loss: {train_metrics['loss']:.4f}")
                    print(f"Val Loss: {val_metrics['loss']:.4f}")
                    if 'accuracy' in val_metrics:
                        print(f"Val Accuracy: {val_metrics['accuracy']:.4f}")
                
                # Checkpointing
                is_best = val_metrics['loss'] < self.best_val_loss
                self.save_checkpoint(is_best=is_best, extra_info={
                    'train_metrics': train_metrics,
                    'val_metrics': val_metrics
                })
                
                # Early stopping
                if self.check_early_stopping(val_metrics):
                    print("🛑 Early stopping triggered")
                    break
        
        print("\n✅ Training completed!")
        
        # Save final metrics
        if self.rank == 0:
            metrics_path = self.checkpoint_dir / "training_metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump({
                    'train_metrics': {k: [float(v) for v in vals] for k, vals in self.train_metrics.items()},
                    'val_metrics': {k: [float(v) for v in vals] for k, vals in self.val_metrics.items()}
                }, f, indent=2)


def setup_distributed(rank: int, world_size: int):
    """Setup for distributed training."""
    import os
    
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'
    
    # Initialize process group
    dist.init_process_group("nccl", rank=rank, world_size=world_size)


def cleanup_distributed():
    """Cleanup distributed training."""
    dist.destroy_process_group()


def create_optimizer(model: nn.Module, config: Dict) -> optim.Optimizer:
    """Create optimizer with advanced features."""
    optimizer_type = config.get('optimizer', 'adamw')
    lr = config.get('learning_rate', 1e-4)
    weight_decay = config.get('weight_decay', 0.01)
    
    # Separate parameters for weight decay
    no_decay = ['bias', 'LayerNorm.weight', 'layer_norm.weight']
    optimizer_grouped_parameters = [
        {
            'params': [p for n, p in model.named_parameters() 
                      if not any(nd in n for nd in no_decay)],
            'weight_decay': weight_decay
        },
        {
            'params': [p for n, p in model.named_parameters() 
                      if any(nd in n for nd in no_decay)],
            'weight_decay': 0.0
        }
    ]
    
    if optimizer_type == 'adamw':
        return optim.AdamW(optimizer_grouped_parameters, lr=lr, betas=(0.9, 0.999), eps=1e-8)
    elif optimizer_type == 'adam':
        return optim.Adam(optimizer_grouped_parameters, lr=lr)
    elif optimizer_type == 'sgd':
        return optim.SGD(optimizer_grouped_parameters, lr=lr, momentum=0.9, nesterov=True)
    elif optimizer_type == 'lamb':
        # LAMB optimizer for large batch training
        try:
            from torch_optimizer import Lamb
            return Lamb(optimizer_grouped_parameters, lr=lr, weight_decay=weight_decay)
        except ImportError:
            print("Warning: LAMB optimizer not available, falling back to AdamW")
            return optim.AdamW(optimizer_grouped_parameters, lr=lr)
    else:
        return optim.AdamW(optimizer_grouped_parameters, lr=lr)


if __name__ == "__main__":
    print("✅ Advanced training infrastructure initialized")
    
    # Example usage
    from torch.utils.data import TensorDataset
    
    # Dummy model
    model = nn.Sequential(
        nn.Linear(128, 256),
        nn.ReLU(),
        nn.Linear(256, 3)
    )
    
    # Dummy data
    X = torch.randn(1000, 128)
    y = torch.randint(0, 3, (1000,))
    train_dataset = TensorDataset(X[:800], y[:800])
    val_dataset = TensorDataset(X[800:], y[800:])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    
    # Config
    config = {
        'learning_rate': 1e-3,
        'weight_decay': 0.01,
        'optimizer': 'adamw',
        'scheduler': 'cosine',
        'gradient_accumulation_steps': 2,
        'max_grad_norm': 1.0,
        'early_stopping_patience': 5,
        'log_interval': 10
    }
    
    # Criterion
    criterion = nn.CrossEntropyLoss()
    
    # Optimizer
    optimizer = create_optimizer(model, config)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    print(f"Device: {device}")
    print("✅ Trainer test setup complete")
