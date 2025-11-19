"""
Multimodal Learning for Scientific Paper Analysis.

Combines:
- Text (abstracts, claims)
- Vision (figures, charts, tables from papers)
- Structured data (metadata, citations)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
from transformers import CLIPModel, CLIPProcessor
import torchvision.models as models


class MultimodalFusion(nn.Module):
    """
    Multimodal fusion module for combining different modalities.
    
    Supports:
    - Early fusion (concat features)
    - Late fusion (ensemble decisions)
    - Cross-modal attention
    """
    
    def __init__(
        self,
        text_dim: int = 768,
        vision_dim: int = 2048,
        struct_dim: int = 128,
        hidden_dim: int = 512,
        fusion_method: str = 'attention'
    ):
        """
        Initialize fusion module.
        
        Args:
            text_dim: Text feature dimension
            vision_dim: Vision feature dimension
            struct_dim: Structured data dimension
            hidden_dim: Hidden dimension for fusion
            fusion_method: 'concat', 'attention', 'gated', 'tensor'
        """
        super().__init__()
        self.fusion_method = fusion_method
        
        # Projection layers
        self.text_proj = nn.Linear(text_dim, hidden_dim)
        self.vision_proj = nn.Linear(vision_dim, hidden_dim)
        self.struct_proj = nn.Linear(struct_dim, hidden_dim)
        
        if fusion_method == 'attention':
            # Cross-modal attention
            self.attention = nn.MultiheadAttention(
                embed_dim=hidden_dim,
                num_heads=8,
                dropout=0.1,
                batch_first=True
            )
            self.norm = nn.LayerNorm(hidden_dim)
        
        elif fusion_method == 'gated':
            # Gated fusion
            self.gate_text = nn.Sequential(
                nn.Linear(hidden_dim * 3, hidden_dim),
                nn.Sigmoid()
            )
            self.gate_vision = nn.Sequential(
                nn.Linear(hidden_dim * 3, hidden_dim),
                nn.Sigmoid()
            )
            self.gate_struct = nn.Sequential(
                nn.Linear(hidden_dim * 3, hidden_dim),
                nn.Sigmoid()
            )
        
        elif fusion_method == 'tensor':
            # Tucker decomposition for tensor fusion
            self.tucker_core = nn.Parameter(torch.randn(hidden_dim, hidden_dim, hidden_dim, hidden_dim))
            
        # Output projection
        if fusion_method == 'concat':
            self.output_proj = nn.Linear(hidden_dim * 3, hidden_dim)
        else:
            self.output_proj = nn.Linear(hidden_dim, hidden_dim)
    
    def forward(
        self,
        text_features: torch.Tensor,
        vision_features: Optional[torch.Tensor] = None,
        struct_features: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Fuse multimodal features.
        
        Args:
            text_features: [B, text_dim] or [B, L, text_dim]
            vision_features: [B, vision_dim] or [B, K, vision_dim]
            struct_features: [B, struct_dim]
            
        Returns:
            Fused features [B, hidden_dim]
        """
        # Project to common dimension
        text_proj = self.text_proj(text_features)
        
        # Handle sequence inputs
        if text_proj.dim() == 3:
            text_proj = text_proj.mean(dim=1)
        
        if vision_features is not None:
            vision_proj = self.vision_proj(vision_features)
            if vision_proj.dim() == 3:
                vision_proj = vision_proj.mean(dim=1)
        else:
            vision_proj = torch.zeros_like(text_proj)
        
        if struct_features is not None:
            struct_proj = self.struct_proj(struct_features)
        else:
            struct_proj = torch.zeros_like(text_proj)
        
        # Fusion
        if self.fusion_method == 'concat':
            # Simple concatenation
            fused = torch.cat([text_proj, vision_proj, struct_proj], dim=-1)
            fused = self.output_proj(fused)
        
        elif self.fusion_method == 'attention':
            # Cross-modal attention
            # Stack modalities
            multimodal = torch.stack([text_proj, vision_proj, struct_proj], dim=1)  # [B, 3, H]
            
            # Self-attention across modalities
            attended, _ = self.attention(multimodal, multimodal, multimodal)
            attended = self.norm(attended + multimodal)
            
            # Pool
            fused = attended.mean(dim=1)
        
        elif self.fusion_method == 'gated':
            # Gated fusion
            all_features = torch.cat([text_proj, vision_proj, struct_proj], dim=-1)
            
            gate_t = self.gate_text(all_features)
            gate_v = self.gate_vision(all_features)
            gate_s = self.gate_struct(all_features)
            
            fused = gate_t * text_proj + gate_v * vision_proj + gate_s * struct_proj
        
        elif self.fusion_method == 'tensor':
            # Tensor fusion (simplified)
            # Bilinear interaction
            tv = torch.einsum('bi,bj->bij', text_proj, vision_proj)
            tvs = torch.einsum('bij,bk->bijk', tv, struct_proj)
            
            # Contract with core tensor
            fused = torch.einsum('bijk,ijkl->bl', tvs, self.tucker_core)
        
        else:
            # Average fusion
            fused = (text_proj + vision_proj + struct_proj) / 3
        
        return self.output_proj(fused) if self.fusion_method != 'concat' else fused


class VisionEncoder(nn.Module):
    """Vision encoder for scientific figures and tables."""
    
    def __init__(self, model_name: str = 'resnet50', pretrained: bool = True):
        super().__init__()
        
        if model_name == 'resnet50':
            self.backbone = models.resnet50(pretrained=pretrained)
            self.feature_dim = 2048
            # Remove classification head
            self.backbone = nn.Sequential(*list(self.backbone.children())[:-1])
        
        elif model_name == 'clip':
            # Use CLIP vision encoder
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.backbone = self.clip_model.vision_model
            self.feature_dim = 768
        
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        Encode images.
        
        Args:
            images: [B, 3, H, W] image tensor
            
        Returns:
            Image features [B, feature_dim]
        """
        if hasattr(self, 'clip_model'):
            features = self.backbone(pixel_values=images).pooler_output
        else:
            features = self.backbone(images)
            features = features.squeeze(-1).squeeze(-1)
        
        return features


class MultimodalCausalModel(nn.Module):
    """Complete multimodal model for causal claim verification."""
    
    def __init__(
        self,
        text_encoder: nn.Module,
        vision_encoder: Optional[nn.Module] = None,
        struct_dim: int = 128,
        hidden_dim: int = 512,
        num_classes: int = 3,
        fusion_method: str = 'attention'
    ):
        super().__init__()
        
        self.text_encoder = text_encoder
        self.vision_encoder = vision_encoder
        
        # Determine feature dimensions
        # Assume text encoder outputs dict with 'embeddings'
        text_dim = hidden_dim  # Will be determined from encoder
        vision_dim = vision_encoder.feature_dim if vision_encoder else 0
        
        # Fusion module
        self.fusion = MultimodalFusion(
            text_dim=text_dim,
            vision_dim=vision_dim if vision_dim > 0 else text_dim,
            struct_dim=struct_dim,
            hidden_dim=hidden_dim,
            fusion_method=fusion_method
        )
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, num_classes)
        )
        
        # Auxiliary heads for multi-task learning
        self.causal_head = nn.Linear(hidden_dim, 2)  # Causal vs non-causal
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        text_inputs: Dict[str, torch.Tensor],
        images: Optional[torch.Tensor] = None,
        struct_features: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            text_inputs: Dict with 'input_ids', 'attention_mask'
            images: [B, 3, H, W] images (optional)
            struct_features: [B, struct_dim] structured features (optional)
            
        Returns:
            Dict with logits and auxiliary outputs
        """
        # Encode text
        text_output = self.text_encoder(**text_inputs)
        if isinstance(text_output, dict):
            text_features = text_output['embeddings']
        else:
            text_features = text_output
        
        # Encode images
        if images is not None and self.vision_encoder is not None:
            vision_features = self.vision_encoder(images)
        else:
            vision_features = None
        
        # Fuse modalities
        fused_features = self.fusion(text_features, vision_features, struct_features)
        
        # Predictions
        logits = self.classifier(fused_features)
        causal_logits = self.causal_head(fused_features)
        confidence = self.confidence_head(fused_features)
        
        return {
            'logits': logits,
            'causal_logits': causal_logits,
            'confidence': confidence,
            'fused_features': fused_features
        }


class TableEncoder(nn.Module):
    """Encoder for tabular data from scientific papers."""
    
    def __init__(self, hidden_dim: int = 256):
        super().__init__()
        
        # Row encoder (process each row)
        self.row_encoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, hidden_dim)
        )
        
        # Column encoder (aggregate columns)
        self.col_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=8,
            batch_first=True
        )
        
        # Table-level aggregation
        self.table_pooling = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )
    
    def forward(self, table_embeddings: torch.Tensor) -> torch.Tensor:
        """
        Encode table.
        
        Args:
            table_embeddings: [B, R, C, D] where R=rows, C=cols, D=dim
            
        Returns:
            Table features [B, D]
        """
        B, R, C, D = table_embeddings.shape
        
        # Encode each row
        table_flat = table_embeddings.view(B * R, C, D)
        row_encoded = self.row_encoder(table_flat)  # [B*R, C, D]
        
        # Attention over columns
        col_attended, _ = self.col_attention(row_encoded, row_encoded, row_encoded)
        col_pooled = col_attended.mean(dim=1)  # [B*R, D]
        
        # Reshape back
        col_pooled = col_pooled.view(B, R, D)
        
        # Pool over rows
        table_features = col_pooled.mean(dim=1)  # [B, D]
        table_features = self.table_pooling(table_features)
        
        return table_features


class FigureTextMatcher(nn.Module):
    """Match figures with captions/mentions in text."""
    
    def __init__(self, text_dim: int = 768, vision_dim: int = 2048, hidden_dim: int = 512):
        super().__init__()
        
        self.text_proj = nn.Linear(text_dim, hidden_dim)
        self.vision_proj = nn.Linear(vision_dim, hidden_dim)
        
        # Matching score
        self.matcher = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        text_features: torch.Tensor,
        vision_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute matching scores.
        
        Args:
            text_features: [B, text_dim]
            vision_features: [B, vision_dim]
            
        Returns:
            Matching scores [B]
        """
        text_proj = self.text_proj(text_features)
        vision_proj = self.vision_proj(vision_features)
        
        # Concatenate
        combined = torch.cat([text_proj, vision_proj], dim=-1)
        
        # Matching score
        score = self.matcher(combined).squeeze(-1)
        
        return score


class MultimodalContrastiveLearning(nn.Module):
    """Contrastive learning across modalities."""
    
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature
    
    def forward(
        self,
        text_features: torch.Tensor,
        vision_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute contrastive loss between text and vision.
        
        Args:
            text_features: [B, D] normalized text features
            vision_features: [B, D] normalized vision features
            
        Returns:
            Contrastive loss
        """
        # Normalize
        text_features = F.normalize(text_features, p=2, dim=1)
        vision_features = F.normalize(vision_features, p=2, dim=1)
        
        # Compute similarity matrix
        similarity = torch.matmul(text_features, vision_features.T) / self.temperature
        
        # Labels (diagonal should match)
        batch_size = text_features.shape[0]
        labels = torch.arange(batch_size, device=text_features.device)
        
        # Symmetric loss
        loss_text_to_vision = F.cross_entropy(similarity, labels)
        loss_vision_to_text = F.cross_entropy(similarity.T, labels)
        
        loss = (loss_text_to_vision + loss_vision_to_text) / 2
        
        return loss


if __name__ == "__main__":
    print("✅ Multimodal learning modules initialized")
    
    # Test vision encoder
    vision_encoder = VisionEncoder(model_name='resnet50')
    dummy_images = torch.randn(4, 3, 224, 224)
    features = vision_encoder(dummy_images)
    print(f"Vision features shape: {features.shape}")
    
    # Test fusion
    fusion = MultimodalFusion(
        text_dim=768,
        vision_dim=2048,
        struct_dim=128,
        hidden_dim=512,
        fusion_method='attention'
    )
    
    text_feat = torch.randn(4, 768)
    vision_feat = torch.randn(4, 2048)
    struct_feat = torch.randn(4, 128)
    
    fused = fusion(text_feat, vision_feat, struct_feat)
    print(f"Fused features shape: {fused.shape}")
    
    # Test table encoder
    table_encoder = TableEncoder(hidden_dim=256)
    table_data = torch.randn(2, 10, 5, 256)  # 2 tables, 10 rows, 5 cols, 256 dim
    table_features = table_encoder(table_data)
    print(f"Table features shape: {table_features.shape}")
    
    print("✅ Multimodal learning ready!")
