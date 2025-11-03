"""
GNN processor for end-to-end graph processing and prediction.
Orchestrates embedding, model inference, and risk/relevance scoring.
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import structlog
from pathlib import Path
from torch_geometric.data import Data

from gnn_app.models.gnn_model import PredictiveGNN, create_model
from gnn_app.services.embedding_service import get_embedding_service
from gnn_app.core.graph_schema import TemporalGraph, GraphNode, GraphEdge, RiskLevel
from gnn_app.config import settings

logger = structlog.get_logger()


class GNNProcessor:
    """
    Main processor for GNN-based graph analysis.
    Handles the full pipeline from graph to predictions.
    """
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: str = "cpu"
    ):
        """
        Initialize GNN processor.
        
        Args:
            model_path: Path to pretrained model (optional)
            device: Device to run on (cpu/cuda)
        """
        self.device = device
        self.embedding_service = get_embedding_service()
        
        # Create or load model
        model_config = {
            'input_dim': self.embedding_service.embedding_dim,
            'hidden_dim': settings.gnn.hidden_dim,
            'num_layers': settings.gnn.num_layers,
            'dropout': settings.gnn.dropout,
            'aggregation': settings.gnn.aggregation
        }
        
        self.model = create_model(model_config).to(device)
        
        if model_path and model_path.exists():
            self.load_model(model_path)
            logger.info("Loaded pretrained model", path=model_path)
        else:
            logger.info("Initialized new model")
        
        self.model.eval()
    
    def process_graph(
        self,
        graph: TemporalGraph,
        compute_embeddings: bool = True
    ) -> TemporalGraph:
        """
        Process a temporal graph through the GNN pipeline.
        
        Args:
            graph: Input temporal graph
            compute_embeddings: Whether to compute node embeddings
            
        Returns:
            Graph with updated predictions
        """
        logger.info("Processing graph", nodes=graph.total_nodes, edges=graph.total_edges)
        
        # Prepare data
        pyg_data = self._graph_to_pyg(graph, compute_embeddings)
        
        # Run inference
        with torch.no_grad():
            predictions = self.model(
                pyg_data.x,
                pyg_data.edge_index,
                return_embeddings=True
            )
        
        # Update graph with predictions
        self._update_graph_predictions(graph, predictions)
        
        # Compute additional metrics
        self._compute_graph_metrics(graph)
        
        logger.info("Graph processing complete")
        
        return graph
    
    def _graph_to_pyg(
        self,
        graph: TemporalGraph,
        compute_embeddings: bool = True
    ) -> Data:
        """
        Convert temporal graph to PyTorch Geometric Data.
        
        Args:
            graph: Temporal graph
            compute_embeddings: Whether to compute embeddings
            
        Returns:
            PyG Data object
        """
        # Get node list (consistent ordering)
        node_list = list(graph.nodes.keys())
        node_to_idx = {nid: idx for idx, nid in enumerate(node_list)}
        
        # Compute node features (embeddings)
        if compute_embeddings:
            nodes = [graph.nodes[nid] for nid in node_list]
            embeddings = self.embedding_service.embed_nodes_batch(nodes)
        else:
            # Use existing embeddings
            embeddings = np.array([
                graph.nodes[nid].embedding if graph.nodes[nid].embedding
                else np.zeros(self.embedding_service.embedding_dim)
                for nid in node_list
            ])
        
        x = torch.tensor(embeddings, dtype=torch.float32)
        
        # Build edge index
        edge_index = []
        for edge in graph.edges:
            if edge.source_id in node_to_idx and edge.target_id in node_to_idx:
                src_idx = node_to_idx[edge.source_id]
                tgt_idx = node_to_idx[edge.target_id]
                edge_index.append([src_idx, tgt_idx])
                # Add reverse edge for undirected graph
                edge_index.append([tgt_idx, src_idx])
        
        if edge_index:
            edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        else:
            edge_index = torch.zeros((2, 0), dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index)
        data.node_ids = node_list  # Store node IDs for mapping back
        
        return data.to(self.device)
    
    def _update_graph_predictions(
        self,
        graph: TemporalGraph,
        predictions: Dict[str, torch.Tensor]
    ):
        """
        Update graph nodes with predictions from model.
        
        Args:
            graph: Temporal graph to update
            predictions: Model predictions
        """
        risk_scores = predictions['risk_scores'].cpu().numpy()
        risk_logits = predictions['risk_logits'].cpu().numpy()
        relevance_scores = predictions['relevance_scores'].cpu().numpy()
        embeddings = predictions['embeddings'].cpu().numpy()
        
        node_list = list(graph.nodes.keys())
        
        for idx, node_id in enumerate(node_list):
            node = graph.nodes[node_id]
            
            # Update scores
            node.risk_score = float(risk_scores[idx])
            node.relevance_score = float(relevance_scores[idx])
            node.embedding = embeddings[idx].tolist()
            
            # Update risk level
            risk_probs = torch.softmax(
                torch.tensor(risk_logits[idx]),
                dim=0
            ).numpy()
            risk_level_idx = np.argmax(risk_probs)
            risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            node.risk_level = risk_levels[risk_level_idx]
            
            # Mark as critical if high risk
            if node.risk_score > 0.8:
                node.is_critical = True
    
    def _compute_graph_metrics(self, graph: TemporalGraph):
        """
        Compute additional graph-level metrics.
        
        Args:
            graph: Temporal graph
        """
        # Compute edge risk contributions
        for edge in graph.edges:
            source = graph.nodes.get(edge.source_id)
            target = graph.nodes.get(edge.target_id)
            
            if source and target:
                # Risk contribution is average of connected node risks
                edge.risk_contribution = (source.risk_score + target.risk_score) / 2
                
                # Mark as anomalous if high risk difference
                risk_diff = abs(source.risk_score - target.risk_score)
                if risk_diff > 0.4:
                    edge.is_anomalous = True
    
    def forecast_temporal_risk(
        self,
        graph: TemporalGraph,
        node_id: str,
        months_ahead: int = 3
    ) -> float:
        """
        Forecast future risk for a node.
        
        Args:
            graph: Temporal graph
            node_id: Node to forecast
            months_ahead: Months to forecast ahead
            
        Returns:
            Forecasted risk score
        """
        node = graph.nodes.get(node_id)
        if not node:
            return 0.0
        
        # Simple forecasting based on current trend
        # In production, this would use the temporal forecaster with historical data
        if node.activity_trend:
            # Linear extrapolation of trend
            trend = np.array(node.activity_trend)
            if len(trend) > 1:
                slope = (trend[-1] - trend[0]) / len(trend)
                forecast = node.risk_score + (slope * months_ahead)
                return float(np.clip(forecast, 0.0, 1.0))
        
        # Default: current risk + small random walk
        forecast = node.risk_score + np.random.normal(0, 0.1)
        return float(np.clip(forecast, 0.0, 1.0))
    
    def find_investigation_path(
        self,
        graph: TemporalGraph,
        start_node_id: str,
        max_depth: int = 3,
        min_risk: float = 0.5
    ) -> List[GraphNode]:
        """
        Find investigation path from a starting node.
        Uses BFS to find high-risk connected nodes.
        
        Args:
            graph: Temporal graph
            start_node_id: Starting node ID
            max_depth: Maximum path depth
            min_risk: Minimum risk threshold
            
        Returns:
            List of nodes in investigation path
        """
        if start_node_id not in graph.nodes:
            return []
        
        visited = set()
        path = []
        queue = [(start_node_id, 0)]
        
        while queue:
            node_id, depth = queue.pop(0)
            
            if node_id in visited or depth > max_depth:
                continue
            
            visited.add(node_id)
            node = graph.nodes[node_id]
            
            if node.risk_score >= min_risk:
                path.append(node)
            
            # Add neighbors
            neighbors = graph.get_node_neighbors(node_id)
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    neighbor = graph.nodes[neighbor_id]
                    if neighbor.risk_score >= min_risk:
                        queue.append((neighbor_id, depth + 1))
        
        # Sort by risk score
        path.sort(key=lambda n: n.risk_score, reverse=True)
        
        return path
    
    def get_critical_files(
        self,
        graph: TemporalGraph,
        top_k: int = 10
    ) -> List[GraphNode]:
        """
        Get the most critical files from the graph.
        
        Args:
            graph: Temporal graph
            top_k: Number of files to return
            
        Returns:
            List of critical file nodes
        """
        from gnn_app.core.graph_schema import NodeType
        
        file_nodes = [
            node for node in graph.nodes.values()
            if node.type == NodeType.FILE
        ]
        
        # Sort by relevance and risk
        file_nodes.sort(
            key=lambda n: (n.relevance_score + n.risk_score) / 2,
            reverse=True
        )
        
        return file_nodes[:top_k]
    
    def save_model(self, path: Path):
        """Save model checkpoint."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': {
                'input_dim': self.embedding_service.embedding_dim,
                'hidden_dim': settings.gnn.hidden_dim,
                'num_layers': settings.gnn.num_layers,
                'dropout': settings.gnn.dropout,
                'aggregation': settings.gnn.aggregation
            }
        }, path)
        logger.info("Model saved", path=path)
    
    def load_model(self, path: Path):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        logger.info("Model loaded", path=path)


# Global processor instance
_gnn_processor: Optional[GNNProcessor] = None


def get_gnn_processor() -> GNNProcessor:
    """Get or create the global GNN processor instance."""
    global _gnn_processor
    if _gnn_processor is None:
        _gnn_processor = GNNProcessor()
    return _gnn_processor
