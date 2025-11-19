"""Advanced NLP models: BioBERT, SciBERT, PubMedBERT with ensemble methods."""

import torch
import torch.nn as nn
from transformers import (
    AutoModel, AutoTokenizer, AutoConfig,
    BertModel, BertTokenizer
)
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path


class BiomedicalTransformerEnsemble(nn.Module):
    """Ensemble of biomedical transformers for robust predictions."""

    def __init__(self, 
                 models: List[str] = None,
                 num_labels: int = 3,
                 ensemble_method: str = 'weighted_average'):
        """
        Initialize ensemble of biomedical transformers.
        
        Args:
            models: List of model names/paths
            num_labels: Number of output labels
            ensemble_method: 'weighted_average', 'voting', 'stacking'
        """
        super().__init__()
        
        if models is None:
            models = [
                'dmis-lab/biobert-v1.1',  # BioBERT
                'allenai/scibert_scivocab_uncased',  # SciBERT
                'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract'  # PubMedBERT
            ]
        
        self.model_names = models
        self.num_models = len(models)
        self.num_labels = num_labels
        self.ensemble_method = ensemble_method
        
        # Load models
        self.encoders = nn.ModuleList()
        self.classifiers = nn.ModuleList()
        
        for model_name in models:
            try:
                encoder = AutoModel.from_pretrained(model_name)
                hidden_size = encoder.config.hidden_size
                classifier = nn.Sequential(
                    nn.Linear(hidden_size, hidden_size),
                    nn.LayerNorm(hidden_size),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(hidden_size, num_labels)
                )
                self.encoders.append(encoder)
                self.classifiers.append(classifier)
            except Exception as e:
                print(f"Warning: Could not load {model_name}: {e}")
        
        # Ensemble weights (learnable)
        if ensemble_method == 'weighted_average':
            self.ensemble_weights = nn.Parameter(torch.ones(len(self.encoders)) / len(self.encoders))
        
        # Stacking layer for ensemble
        if ensemble_method == 'stacking':
            self.stacking_layer = nn.Sequential(
                nn.Linear(num_labels * len(self.encoders), hidden_size),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_size, num_labels)
            )

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass through ensemble."""
        all_logits = []
        all_embeddings = []
        
        for encoder, classifier in zip(self.encoders, self.classifiers):
            # Get embeddings
            outputs = encoder(input_ids=input_ids, attention_mask=attention_mask)
            pooled_output = outputs.last_hidden_state[:, 0, :]  # CLS token
            
            # Get logits
            logits = classifier(pooled_output)
            
            all_logits.append(logits)
            all_embeddings.append(pooled_output)
        
        # Ensemble predictions
        if self.ensemble_method == 'weighted_average':
            # Normalize weights
            weights = torch.softmax(self.ensemble_weights, dim=0)
            ensemble_logits = sum(w * logits for w, logits in zip(weights, all_logits))
        
        elif self.ensemble_method == 'voting':
            # Majority voting
            ensemble_logits = torch.stack(all_logits).mean(dim=0)
        
        elif self.ensemble_method == 'stacking':
            # Stack predictions and learn combination
            stacked_logits = torch.cat(all_logits, dim=-1)
            ensemble_logits = self.stacking_layer(stacked_logits)
        
        else:
            ensemble_logits = torch.stack(all_logits).mean(dim=0)
        
        return {
            'logits': ensemble_logits,
            'individual_logits': all_logits,
            'embeddings': torch.stack(all_embeddings).mean(dim=0),
            'individual_embeddings': all_embeddings
        }


class CausalTripleExtractor(nn.Module):
    """Advanced causal triple extraction with BioBERT/SciBERT."""

    def __init__(self, 
                 model_name: str = 'dmis-lab/biobert-v1.1',
                 max_length: int = 512):
        super().__init__()
        
        self.model_name = model_name
        self.max_length = max_length
        
        # Load pre-trained model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        
        # Entity span detection heads
        self.entity_start = nn.Linear(hidden_size, 1)
        self.entity_end = nn.Linear(hidden_size, 1)
        
        # Relation classification head
        self.relation_classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, 10)  # 10 causal relation types
        )
        
        # Causal indicators
        self.causal_relations = [
            'causes', 'prevents', 'induces', 'inhibits', 'triggers',
            'leads_to', 'results_in', 'promotes', 'mediates', 'regulates'
        ]

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Extract causal triples from input text."""
        # Get contextualized embeddings
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # [B, L, H]
        
        # Predict entity spans
        start_logits = self.entity_start(sequence_output).squeeze(-1)  # [B, L]
        end_logits = self.entity_end(sequence_output).squeeze(-1)  # [B, L]
        
        # Get pooled representation for relation classification
        pooled_output = outputs.last_hidden_state[:, 0, :]  # CLS token
        
        # Predict relation (simplified - use max pooling for entity pairs)
        entity_repr = sequence_output.max(dim=1)[0]  # Max pooling
        relation_input = torch.cat([pooled_output, entity_repr], dim=-1)
        relation_logits = self.relation_classifier(relation_input)
        
        return {
            'entity_start_logits': start_logits,
            'entity_end_logits': end_logits,
            'relation_logits': relation_logits,
            'embeddings': pooled_output
        }

    def extract_triples(self, text: str, threshold: float = 0.5) -> List[Dict[str, any]]:
        """Extract causal triples from text."""
        # Tokenize
        inputs = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )
        
        # Forward pass
        with torch.no_grad():
            outputs = self.forward(inputs['input_ids'], inputs['attention_mask'])
        
        # Extract entities (simplified - use threshold on logits)
        start_probs = torch.sigmoid(outputs['entity_start_logits'])
        end_probs = torch.sigmoid(outputs['entity_end_logits'])
        
        # Find entity spans
        entities = []
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        for i in range(len(tokens)):
            if start_probs[0, i] > threshold:
                for j in range(i, min(i + 10, len(tokens))):
                    if end_probs[0, j] > threshold:
                        entity_text = self.tokenizer.decode(inputs['input_ids'][0, i:j+1])
                        entities.append({
                            'text': entity_text,
                            'start': i,
                            'end': j,
                            'confidence': float((start_probs[0, i] + end_probs[0, j]) / 2)
                        })
                        break
        
        # Get relation
        relation_idx = torch.argmax(outputs['relation_logits'], dim=-1).item()
        relation = self.causal_relations[relation_idx] if relation_idx < len(self.causal_relations) else 'unknown'
        
        # Create triples
        triples = []
        for i in range(0, len(entities) - 1, 2):
            subject = entities[i]
            obj = entities[i + 1] if i + 1 < len(entities) else None
            if obj:
                triple = {
                    'subject': subject['text'],
                    'relation': relation,
                    'object': obj['text'],
                    'confidence': (subject['confidence'] + obj['confidence']) / 2
                }
                triples.append(triple)
        
        return triples


class ScientificClaimClassifier(nn.Module):
    """Multi-task classifier for scientific claims."""

    def __init__(self, model_name: str = 'allenai/scibert_scivocab_uncased'):
        super().__init__()
        
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        
        # Multi-task heads
        # 1. Causal vs Non-causal
        self.causal_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, 2)
        )
        
        # 2. Claim veracity (SUPPORTS, REFUTES, NOT_ENOUGH_INFO)
        self.veracity_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, 3)
        )
        
        # 3. Domain classification
        self.domain_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, 5)  # medicine, biology, chemistry, physics, other
        )
        
        # 4. Confidence estimation
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Multi-task forward pass."""
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        
        return {
            'causal_logits': self.causal_head(pooled_output),
            'veracity_logits': self.veracity_head(pooled_output),
            'domain_logits': self.domain_head(pooled_output),
            'confidence': self.confidence_head(pooled_output),
            'embeddings': pooled_output
        }


class ContrastiveLearningModel(nn.Module):
    """Contrastive learning for causal claim similarity."""

    def __init__(self, model_name: str = 'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract'):
        super().__init__()
        
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        
        # Projection head for contrastive learning
        self.projection = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 256)  # Projection dimension
        )
        
        self.temperature = 0.07  # Temperature parameter for contrastive loss

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Get embeddings for contrastive learning."""
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        
        # Project to lower dimension
        embeddings = self.projection(pooled_output)
        
        # L2 normalize
        embeddings = nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings

    def contrastive_loss(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """Compute NT-Xent (normalized temperature-scaled cross entropy) loss."""
        batch_size = embeddings.shape[0]
        
        # Compute similarity matrix
        similarity_matrix = torch.matmul(embeddings, embeddings.T) / self.temperature
        
        # Create mask for positive pairs
        labels = labels.unsqueeze(1)
        mask = torch.eq(labels, labels.T).float()
        
        # Remove diagonal (self-similarity)
        mask = mask - torch.eye(batch_size, device=mask.device)
        
        # Compute loss
        exp_sim = torch.exp(similarity_matrix)
        log_prob = similarity_matrix - torch.log(exp_sim.sum(dim=1, keepdim=True))
        
        # Mean log-likelihood over positive pairs
        loss = -(mask * log_prob).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        loss = loss.mean()
        
        return loss


def load_pretrained_model(model_type: str, checkpoint_path: Optional[Path] = None):
    """Load pre-trained biomedical model."""
    model_map = {
        'biobert': 'dmis-lab/biobert-v1.1',
        'scibert': 'allenai/scibert_scivocab_uncased',
        'pubmedbert': 'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract',
        'bluebert': 'bionlp/bluebert_pubmed_mimic_uncased_L-12_H-768_A-12'
    }
    
    model_name = model_map.get(model_type.lower(), model_type)
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        
        if checkpoint_path and checkpoint_path.exists():
            checkpoint = torch.load(checkpoint_path)
            model.load_state_dict(checkpoint['model_state'])
        
        return model, tokenizer
    
    except Exception as e:
        print(f"Error loading {model_type}: {e}")
        return None, None


if __name__ == "__main__":
    print("✅ Advanced NLP models initialized")
    
    # Test ensemble
    try:
        ensemble = BiomedicalTransformerEnsemble(
            models=['dmis-lab/biobert-v1.1'],  # Test with single model
            num_labels=3
        )
        print(f"✅ Ensemble model created with {len(ensemble.encoders)} models")
    except Exception as e:
        print(f"Note: {e}")
    
    # Test triple extractor
    try:
        extractor = CausalTripleExtractor(model_name='dmis-lab/biobert-v1.1')
        print("✅ Causal triple extractor initialized")
    except Exception as e:
        print(f"Note: {e}")
