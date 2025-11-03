"""
Graph Neural Network model for predictive data mapping.
Implements a multi-layer GNN with message passing for risk and relevance prediction.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, SAGEConv, global_mean_pool
from torch_geometric.data import Data, Batch
from typing import Optional, Tuple, List
import numpy as np


class GNNEncoder(nn.Module):
    """
    GNN encoder that learns node embeddings through message passing.
    Supports multiple aggregation methods (GCN, GAT, GraphSAGE).
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.1,
        aggregation: str = "gcn",
        num_heads: int = 4
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.aggregation = aggregation
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # GNN layers
        self.conv_layers = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        
        for i in range(num_layers):
            if aggregation == "gcn":
                conv = GCNConv(hidden_dim, hidden_dim)
            elif aggregation == "gat":
                conv = GATConv(
                    hidden_dim, 
                    hidden_dim // num_heads,
                    heads=num_heads,
                    dropout=dropout
                )
            elif aggregation == "sage":
                conv = SAGEConv(hidden_dim, hidden_dim)
            else:
                raise ValueError(f"Unknown aggregation method: {aggregation}")
            
            self.conv_layers.append(conv)
            self.batch_norms.append(nn.BatchNorm1d(hidden_dim))
        
        self.dropout_layer = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GNN encoder.
        
        Args:
            x: Node features [num_nodes, input_dim]
            edge_index: Edge indices [2, num_edges]
            
        Returns:
            Node embeddings [num_nodes, hidden_dim]
        """
        # Project to hidden dimension
        h = self.input_proj(x)
        h = F.relu(h)
        
        # Apply GNN layers with residual connections
        for i, (conv, bn) in enumerate(zip(self.conv_layers, self.batch_norms)):
            h_prev = h
            h = conv(h, edge_index)
            h = bn(h)
            h = F.relu(h)
            h = self.dropout_layer(h)
            
            # Residual connection (skip connection)
            if i > 0:
                h = h + h_prev
        
        return h


class RiskPredictor(nn.Module):
    """
    Predicts risk score and risk level for each node.
    """
    
    def __init__(self, hidden_dim: int, num_risk_levels: int = 4):
        super().__init__()
        
        # Risk score regression (0-1)
        self.risk_score_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # Output in [0, 1]
        )
        
        # Risk level classification (low, medium, high, critical)
        self.risk_level_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, num_risk_levels)
        )
    
    def forward(self, node_embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict risk scores and levels.
        
        Args:
            node_embeddings: [num_nodes, hidden_dim]
            
        Returns:
            risk_scores: [num_nodes, 1]
            risk_logits: [num_nodes, num_risk_levels]
        """
        risk_scores = self.risk_score_head(node_embeddings)
        risk_logits = self.risk_level_head(node_embeddings)
        return risk_scores, risk_logits


class RelevancePredictor(nn.Module):
    """
    Predicts relevance score for each node.
    """
    
    def __init__(self, hidden_dim: int):
        super().__init__()
        
        self.relevance_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # Output in [0, 1]
        )
    
    def forward(self, node_embeddings: torch.Tensor) -> torch.Tensor:
        """
        Predict relevance scores.
        
        Args:
            node_embeddings: [num_nodes, hidden_dim]
            
        Returns:
            relevance_scores: [num_nodes, 1]
        """
        return self.relevance_head(node_embeddings)


class TemporalForecaster(nn.Module):
    """
    Forecasts future risk based on temporal patterns.
    Uses LSTM on historical embeddings.
    """
    
    def __init__(self, hidden_dim: int, sequence_length: int = 10):
        super().__init__()
        
        self.sequence_length = sequence_length
        
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.1
        )
        
        self.forecast_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, embedding_sequence: torch.Tensor) -> torch.Tensor:
        """
        Forecast future risk from embedding sequence.
        
        Args:
            embedding_sequence: [batch, sequence_length, hidden_dim]
            
        Returns:
            forecasted_risk: [batch, 1]
        """
        lstm_out, _ = self.lstm(embedding_sequence)
        last_hidden = lstm_out[:, -1, :]  # Take last timestep
        forecast = self.forecast_head(last_hidden)
        return forecast


class PredictiveGNN(nn.Module):
    """
    Complete GNN model for predictive data mapping.
    Combines encoding, risk prediction, relevance scoring, and temporal forecasting.
    """
    
    def __init__(
        self,
        input_dim: int = 384,  # Sentence-transformer embedding size
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.1,
        aggregation: str = "gcn",
        num_risk_levels: int = 4
    ):
        super().__init__()
        
        self.encoder = GNNEncoder(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            aggregation=aggregation
        )
        
        self.risk_predictor = RiskPredictor(hidden_dim, num_risk_levels)
        self.relevance_predictor = RelevancePredictor(hidden_dim)
        self.temporal_forecaster = TemporalForecaster(hidden_dim)
    
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        return_embeddings: bool = False
    ) -> dict:
        """
        Full forward pass.
        
        Args:
            x: Node features [num_nodes, input_dim]
            edge_index: Edge indices [2, num_edges]
            return_embeddings: Whether to return node embeddings
            
        Returns:
            Dictionary with predictions
        """
        # Encode nodes
        node_embeddings = self.encoder(x, edge_index)
        
        # Predict risk
        risk_scores, risk_logits = self.risk_predictor(node_embeddings)
        
        # Predict relevance
        relevance_scores = self.relevance_predictor(node_embeddings)
        
        results = {
            'risk_scores': risk_scores.squeeze(-1),
            'risk_logits': risk_logits,
            'relevance_scores': relevance_scores.squeeze(-1),
        }
        
        if return_embeddings:
            results['embeddings'] = node_embeddings
        
        return results
    
    def forecast(
        self,
        embedding_sequence: torch.Tensor
    ) -> torch.Tensor:
        """
        Forecast future risk from historical embeddings.
        
        Args:
            embedding_sequence: [batch, sequence_length, hidden_dim]
            
        Returns:
            forecasted_risk: [batch]
        """
        return self.temporal_forecaster(embedding_sequence).squeeze(-1)
    
    @torch.no_grad()
    def predict_single_node(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        node_idx: int
    ) -> dict:
        """
        Get predictions for a single node.
        
        Args:
            x: Node features [num_nodes, input_dim]
            edge_index: Edge indices [2, num_edges]
            node_idx: Index of node to predict
            
        Returns:
            Dictionary with predictions for the node
        """
        self.eval()
        results = self.forward(x, edge_index, return_embeddings=True)
        
        return {
            'risk_score': results['risk_scores'][node_idx].item(),
            'risk_level_probs': F.softmax(results['risk_logits'][node_idx], dim=0).cpu().numpy(),
            'relevance_score': results['relevance_scores'][node_idx].item(),
            'embedding': results['embeddings'][node_idx].cpu().numpy()
        }


def create_model(config: dict) -> PredictiveGNN:
    """
    Factory function to create a GNN model from config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized PredictiveGNN model
    """
    return PredictiveGNN(
        input_dim=config.get('input_dim', 384),
        hidden_dim=config.get('hidden_dim', 128),
        num_layers=config.get('num_layers', 3),
        dropout=config.get('dropout', 0.1),
        aggregation=config.get('aggregation', 'gcn'),
        num_risk_levels=config.get('num_risk_levels', 4)
    )
