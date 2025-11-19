"""
Uncertainty Quantification for Reliable Predictions.

Implements:
1. Bayesian Neural Networks (variational inference)
2. MC Dropout (Monte Carlo sampling)
3. Deep Ensembles
4. Calibration metrics and recalibration
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.special import softmax


class BayesianLinear(nn.Module):
    """Bayesian Linear Layer with variational inference."""
    
    def __init__(self, in_features: int, out_features: int, prior_std: float = 1.0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        
        # Weight parameters (mean and log variance)
        self.weight_mu = nn.Parameter(torch.randn(out_features, in_features) * 0.01)
        self.weight_logvar = nn.Parameter(torch.randn(out_features, in_features) * 0.01 - 3.0)
        
        # Bias parameters
        self.bias_mu = nn.Parameter(torch.zeros(out_features))
        self.bias_logvar = nn.Parameter(torch.randn(out_features) * 0.01 - 3.0)
        
        # Prior
        self.prior_std = prior_std
        
    def forward(self, x: torch.Tensor, sample: bool = True) -> torch.Tensor:
        """
        Forward pass with reparameterization trick.
        
        Args:
            x: Input tensor
            sample: If True, sample weights; if False, use mean
        """
        if sample and self.training:
            # Sample weights using reparameterization trick
            weight_std = torch.exp(0.5 * self.weight_logvar)
            weight_eps = torch.randn_like(self.weight_mu)
            weight = self.weight_mu + weight_std * weight_eps
            
            bias_std = torch.exp(0.5 * self.bias_logvar)
            bias_eps = torch.randn_like(self.bias_mu)
            bias = self.bias_mu + bias_std * bias_eps
        else:
            # Use mean weights
            weight = self.weight_mu
            bias = self.bias_mu
        
        return F.linear(x, weight, bias)
    
    def kl_divergence(self) -> torch.Tensor:
        """Compute KL divergence between posterior and prior."""
        # KL(q(w) || p(w)) for Gaussian distributions
        weight_kl = 0.5 * torch.sum(
            self.weight_logvar.exp() / (self.prior_std ** 2) +
            (self.weight_mu ** 2) / (self.prior_std ** 2) -
            1 - self.weight_logvar +
            2 * np.log(self.prior_std)
        )
        
        bias_kl = 0.5 * torch.sum(
            self.bias_logvar.exp() / (self.prior_std ** 2) +
            (self.bias_mu ** 2) / (self.prior_std ** 2) -
            1 - self.bias_logvar +
            2 * np.log(self.prior_std)
        )
        
        return weight_kl + bias_kl


class MCDropout(nn.Module):
    """Monte Carlo Dropout for uncertainty estimation."""
    
    def __init__(self, p: float = 0.1):
        super().__init__()
        self.p = p
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply dropout even during inference for MC sampling."""
        return F.dropout(x, p=self.p, training=True)


class BayesianNeuralNetwork(nn.Module):
    """Bayesian Neural Network with variational inference."""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int],
        output_dim: int,
        prior_std: float = 1.0
    ):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(BayesianLinear(prev_dim, hidden_dim, prior_std))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        
        layers.append(BayesianLinear(prev_dim, output_dim, prior_std))
        
        self.layers = nn.ModuleList(layers)
    
    def forward(self, x: torch.Tensor, sample: bool = True) -> torch.Tensor:
        """Forward pass through Bayesian layers."""
        for layer in self.layers:
            if isinstance(layer, BayesianLinear):
                x = layer(x, sample=sample)
            else:
                x = layer(x)
        return x
    
    def kl_divergence(self) -> torch.Tensor:
        """Total KL divergence for all Bayesian layers."""
        kl = 0.0
        for layer in self.layers:
            if isinstance(layer, BayesianLinear):
                kl += layer.kl_divergence()
        return kl
    
    def predict_with_uncertainty(
        self,
        x: torch.Tensor,
        num_samples: int = 100
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict with uncertainty estimation.
        
        Args:
            x: Input tensor
            num_samples: Number of forward passes for uncertainty
            
        Returns:
            Tuple of (mean predictions, uncertainty)
        """
        self.train()  # Enable sampling
        
        predictions = []
        for _ in range(num_samples):
            with torch.no_grad():
                pred = self.forward(x, sample=True)
                predictions.append(pred)
        
        predictions = torch.stack(predictions)
        
        # Mean prediction
        mean_pred = predictions.mean(dim=0)
        
        # Uncertainty (variance)
        uncertainty = predictions.var(dim=0)
        
        return mean_pred, uncertainty


class DeepEnsemble:
    """Deep Ensemble for uncertainty quantification."""
    
    def __init__(self, models: List[nn.Module]):
        """
        Initialize ensemble.
        
        Args:
            models: List of independently trained models
        """
        self.models = models
        self.num_models = len(models)
    
    def predict_with_uncertainty(
        self,
        x: torch.Tensor,
        return_all: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict with ensemble uncertainty.
        
        Args:
            x: Input tensor
            return_all: Return all individual predictions
            
        Returns:
            Tuple of (mean predictions, uncertainty)
        """
        predictions = []
        
        for model in self.models:
            model.eval()
            with torch.no_grad():
                pred = model(x)
                
                # Handle dict outputs
                if isinstance(pred, dict) and 'logits' in pred:
                    pred = pred['logits']
                
                predictions.append(pred)
        
        predictions = torch.stack(predictions)
        
        # Mean prediction
        mean_pred = predictions.mean(dim=0)
        
        # Uncertainty (variance across models)
        uncertainty = predictions.var(dim=0)
        
        if return_all:
            return mean_pred, uncertainty, predictions
        
        return mean_pred, uncertainty


class CalibrationMetrics:
    """Metrics for calibration evaluation."""
    
    @staticmethod
    def expected_calibration_error(
        confidences: np.ndarray,
        predictions: np.ndarray,
        targets: np.ndarray,
        num_bins: int = 10
    ) -> float:
        """
        Compute Expected Calibration Error (ECE).
        
        Args:
            confidences: Predicted confidences [N]
            predictions: Predicted classes [N]
            targets: True classes [N]
            num_bins: Number of bins for calibration
            
        Returns:
            ECE value
        """
        bin_boundaries = np.linspace(0, 1, num_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0.0
        
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Find samples in bin
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                # Accuracy in bin
                accuracy_in_bin = (predictions[in_bin] == targets[in_bin]).mean()
                
                # Average confidence in bin
                avg_confidence_in_bin = confidences[in_bin].mean()
                
                # Add to ECE
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return float(ece)
    
    @staticmethod
    def maximum_calibration_error(
        confidences: np.ndarray,
        predictions: np.ndarray,
        targets: np.ndarray,
        num_bins: int = 10
    ) -> float:
        """
        Compute Maximum Calibration Error (MCE).
        
        Returns maximum gap between confidence and accuracy across bins.
        """
        bin_boundaries = np.linspace(0, 1, num_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        calibration_errors = []
        
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = (predictions[in_bin] == targets[in_bin]).mean()
                avg_confidence_in_bin = confidences[in_bin].mean()
                calibration_errors.append(np.abs(avg_confidence_in_bin - accuracy_in_bin))
        
        if calibration_errors:
            return float(max(calibration_errors))
        return 0.0
    
    @staticmethod
    def brier_score(probabilities: np.ndarray, targets: np.ndarray) -> float:
        """
        Compute Brier Score (mean squared error between probabilities and one-hot targets).
        
        Args:
            probabilities: Predicted probabilities [N, C]
            targets: True class indices [N]
            
        Returns:
            Brier score
        """
        num_classes = probabilities.shape[1]
        one_hot_targets = np.eye(num_classes)[targets]
        
        brier = np.mean(np.sum((probabilities - one_hot_targets) ** 2, axis=1))
        return float(brier)


class TemperatureScaling(nn.Module):
    """Temperature scaling for calibration."""
    
    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
        self.temperature = nn.Parameter(torch.ones(1))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward with temperature scaling."""
        logits = self.model(x)
        
        if isinstance(logits, dict) and 'logits' in logits:
            logits = logits['logits']
        
        return logits / self.temperature
    
    def calibrate(
        self,
        val_loader: torch.utils.data.DataLoader,
        criterion: nn.Module = nn.CrossEntropyLoss()
    ):
        """
        Learn optimal temperature on validation set.
        
        Args:
            val_loader: Validation data loader
            criterion: Loss function
        """
        # Collect validation logits and labels
        logits_list = []
        labels_list = []
        
        self.model.eval()
        with torch.no_grad():
            for batch in val_loader:
                logits = self.model(batch['input'])
                if isinstance(logits, dict) and 'logits' in logits:
                    logits = logits['logits']
                
                logits_list.append(logits)
                labels_list.append(batch['labels'])
        
        logits = torch.cat(logits_list)
        labels = torch.cat(labels_list)
        
        # Optimize temperature
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.01, max_iter=50)
        
        def eval():
            optimizer.zero_grad()
            loss = criterion(self.forward(logits), labels)
            loss.backward()
            return loss
        
        optimizer.step(eval)
        
        print(f"✅ Optimal temperature: {self.temperature.item():.4f}")


class UncertaintyEvaluator:
    """Comprehensive uncertainty evaluation."""
    
    def __init__(self, model: nn.Module, method: str = 'mc_dropout', num_samples: int = 100):
        """
        Initialize evaluator.
        
        Args:
            model: Model to evaluate
            method: 'mc_dropout', 'bayesian', or 'ensemble'
            num_samples: Number of samples for MC methods
        """
        self.model = model
        self.method = method
        self.num_samples = num_samples
    
    def predict_with_uncertainty(
        self,
        x: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Get predictions with uncertainty estimates.
        
        Returns:
            Dictionary with predictions, uncertainty, entropy
        """
        if self.method == 'mc_dropout':
            return self._mc_dropout_predict(x)
        elif self.method == 'bayesian' and isinstance(self.model, BayesianNeuralNetwork):
            return self._bayesian_predict(x)
        elif self.method == 'ensemble' and isinstance(self.model, DeepEnsemble):
            return self._ensemble_predict(x)
        else:
            return self._single_predict(x)
    
    def _mc_dropout_predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """MC Dropout prediction."""
        self.model.train()  # Enable dropout
        
        predictions = []
        for _ in range(self.num_samples):
            with torch.no_grad():
                pred = self.model(x)
                if isinstance(pred, dict) and 'logits' in pred:
                    pred = pred['logits']
                predictions.append(F.softmax(pred, dim=-1))
        
        predictions = torch.stack(predictions)
        
        # Mean prediction
        mean_pred = predictions.mean(dim=0)
        
        # Predictive variance (aleatoric + epistemic)
        variance = predictions.var(dim=0)
        
        # Predictive entropy (epistemic uncertainty)
        entropy = -torch.sum(mean_pred * torch.log(mean_pred + 1e-10), dim=-1)
        
        # Mutual information (epistemic uncertainty)
        mutual_info = entropy - (-predictions * torch.log(predictions + 1e-10)).sum(dim=-1).mean(dim=0)
        
        return {
            'predictions': mean_pred,
            'variance': variance,
            'entropy': entropy,
            'mutual_information': mutual_info,
            'all_samples': predictions
        }
    
    def _bayesian_predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Bayesian prediction."""
        mean_pred, uncertainty = self.model.predict_with_uncertainty(x, self.num_samples)
        
        probs = F.softmax(mean_pred, dim=-1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)
        
        return {
            'predictions': probs,
            'variance': uncertainty,
            'entropy': entropy
        }
    
    def _ensemble_predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Ensemble prediction."""
        mean_pred, uncertainty = self.model.predict_with_uncertainty(x)
        
        probs = F.softmax(mean_pred, dim=-1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)
        
        return {
            'predictions': probs,
            'variance': uncertainty,
            'entropy': entropy
        }
    
    def _single_predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Single model prediction."""
        self.model.eval()
        with torch.no_grad():
            pred = self.model(x)
            if isinstance(pred, dict) and 'logits' in pred:
                pred = pred['logits']
            
            probs = F.softmax(pred, dim=-1)
            entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)
            
            return {
                'predictions': probs,
                'entropy': entropy
            }


if __name__ == "__main__":
    print("✅ Uncertainty quantification modules initialized")
    
    # Test Bayesian NN
    bnn = BayesianNeuralNetwork(
        input_dim=128,
        hidden_dims=[256, 128],
        output_dim=3
    )
    print(f"✅ Bayesian NN created with KL: {bnn.kl_divergence().item():.4f}")
    
    # Test prediction
    x = torch.randn(10, 128)
    mean_pred, uncertainty = bnn.predict_with_uncertainty(x, num_samples=50)
    print(f"Mean prediction shape: {mean_pred.shape}")
    print(f"Uncertainty shape: {uncertainty.shape}")
    
    print("✅ Uncertainty quantification ready!")
