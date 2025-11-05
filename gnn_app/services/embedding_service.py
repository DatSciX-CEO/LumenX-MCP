"""
Embedding service for generating node feature vectors.
Uses local sentence-transformers for text embeddings.
"""

import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Union
import numpy as np
from functools import lru_cache
import structlog

from gnn_app.config import settings
from gnn_app.core.graph_schema import GraphNode, NodeType

logger = structlog.get_logger()


class EmbeddingService:
    """
    Service for generating embeddings from text using local models.
    Supports caching and batch processing.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        cache_size: int = 10000
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of sentence-transformer model
            device: Device to run on (cpu/cuda)
            cache_size: Size of embedding cache
        """
        self.model_name = model_name or settings.embedding.model_name
        self.device = device or settings.embedding.device
        self.cache_size = cache_size
        
        logger.info("Loading embedding model", model=self.model_name, device=self.device)
        
        # Load model
        self.model = SentenceTransformer(self.model_name, device=self.device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        logger.info("Embedding model loaded", embedding_dim=self.embedding_dim)
        
        # Cache for embeddings
        self._cache: Dict[str, np.ndarray] = {}
    
    def embed_text(self, text: Union[str, List[str]], use_cache: bool = True) -> np.ndarray:
        """
        Generate embeddings for text.
        
        Args:
            text: Single text or list of texts
            use_cache: Whether to use cache
            
        Returns:
            Embeddings array
        """
        if isinstance(text, str):
            text = [text]
        
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache
        for i, t in enumerate(text):
            if use_cache and t in self._cache:
                embeddings.append(self._cache[t])
            else:
                texts_to_embed.append(t)
                indices_to_embed.append(i)
                embeddings.append(None)
        
        # Embed uncached texts
        if texts_to_embed:
            new_embeddings = self.model.encode(
                texts_to_embed,
                batch_size=settings.embedding.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Update cache and results
            for idx, text_val, emb in zip(indices_to_embed, texts_to_embed, new_embeddings):
                embeddings[idx] = emb
                if use_cache and len(self._cache) < self.cache_size:
                    self._cache[text_val] = emb
        
        return np.array(embeddings)
    
    def embed_node(self, node: GraphNode) -> np.ndarray:
        """
        Generate embedding for a graph node.
        Creates a rich text representation from node attributes.
        
        Args:
            node: GraphNode to embed
            
        Returns:
            Embedding vector
        """
        # Create text representation
        text_parts = [
            f"Type: {node.type.value}",
            f"Label: {node.label}",
        ]
        
        # Add type-specific information
        if node.type == NodeType.CUSTODIAN:
            text_parts.append(f"Role: {node.metadata.get('role', 'unknown')}")
            text_parts.append(f"Department: {node.metadata.get('department', 'unknown')}")
        elif node.type == NodeType.FILE:
            text_parts.append(f"File type: {node.metadata.get('file_type', 'unknown')}")
            text_parts.append(f"Owner: {node.metadata.get('owner', 'unknown')}")
            if 'tags' in node.metadata:
                text_parts.append(f"Tags: {', '.join(node.metadata['tags'])}")
        elif node.type == NodeType.CHANNEL:
            text_parts.append(f"Channel type: {node.metadata.get('platform', 'unknown')}")
            text_parts.append(f"Members: {node.metadata.get('member_count', 0)}")
        
        # Add description if available
        if 'description' in node.metadata:
            text_parts.append(f"Description: {node.metadata['description']}")
        
        text = " | ".join(text_parts)
        embedding = self.embed_text(text, use_cache=False)[0]
        
        return embedding
    
    def embed_nodes_batch(self, nodes: List[GraphNode]) -> np.ndarray:
        """
        Generate embeddings for multiple nodes in batch.
        
        Args:
            nodes: List of GraphNodes
            
        Returns:
            Array of embeddings [num_nodes, embedding_dim]
        """
        texts = []
        for node in nodes:
            # Create text representation
            text_parts = [f"Type: {node.type.value}", f"Label: {node.label}"]
            
            # Add metadata
            if 'description' in node.metadata:
                text_parts.append(node.metadata['description'])
            
            texts.append(" | ".join(text_parts))
        
        embeddings = self.embed_text(texts, use_cache=False)
        return embeddings
    
    def get_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
    
    def find_similar_nodes(
        self,
        query_embedding: np.ndarray,
        node_embeddings: np.ndarray,
        top_k: int = 10
    ) -> List[int]:
        """
        Find most similar nodes to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            node_embeddings: Array of node embeddings [num_nodes, embedding_dim]
            top_k: Number of top results to return
            
        Returns:
            Indices of top-k most similar nodes
        """
        # Compute similarities
        similarities = np.dot(node_embeddings, query_embedding) / (
            np.linalg.norm(node_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return top_indices.tolist()
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
