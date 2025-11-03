"""
Graph data structures and schema definitions.
Defines nodes, edges, and the temporal knowledge graph structure.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
import numpy as np


class NodeType(str, Enum):
    """Types of nodes in the graph."""
    CUSTODIAN = "custodian"
    FILE = "file"
    CHANNEL = "channel"
    EMAIL = "email"
    DOCUMENT = "document"


class EdgeType(str, Enum):
    """Types of edges (relationships) in the graph."""
    SENT_EMAIL = "sent_email"
    RECEIVED_EMAIL = "received_email"
    ACCESSED_FILE = "accessed_file"
    EDITED_FILE = "edited_file"
    CREATED_FILE = "created_file"
    MEMBER_OF_CHANNEL = "member_of_channel"
    SHARED_IN_CHANNEL = "shared_in_channel"
    COLLABORATED_WITH = "collaborated_with"


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GraphNode(BaseModel):
    """
    Represents a node in the temporal knowledge graph.
    Can be a custodian, file, channel, etc.
    """
    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Type of node")
    label: str = Field(..., description="Display label")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Node-specific metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    
    # GNN computed properties
    embedding: Optional[List[float]] = Field(default=None, description="Node embedding vector")
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Relevance score")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Risk level")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk score (0-1)")
    
    # Graph properties
    degree: int = Field(default=0, description="Node degree (number of connections)")
    in_degree: int = Field(default=0, description="Number of incoming edges")
    out_degree: int = Field(default=0, description="Number of outgoing edges")
    
    # Temporal properties
    activity_trend: List[float] = Field(default_factory=list, description="Activity over time")
    forecasted_risk: Optional[float] = Field(default=None, description="Predicted future risk")
    
    # Investigation flags
    is_flagged: bool = Field(default=False, description="Flagged for review")
    is_critical: bool = Field(default=False, description="Critical entity")
    investigation_notes: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class GraphEdge(BaseModel):
    """
    Represents an edge (relationship) in the temporal knowledge graph.
    """
    id: str = Field(..., description="Unique edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    edge_type: EdgeType = Field(..., description="Type of relationship")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.now, description="When interaction occurred")
    
    # Edge properties
    weight: float = Field(default=1.0, description="Edge weight/strength")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in relationship")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Edge-specific metadata")
    
    # Risk properties
    is_anomalous: bool = Field(default=False, description="Flagged as anomalous")
    risk_contribution: float = Field(default=0.0, description="Contribution to overall risk")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class TemporalGraph(BaseModel):
    """
    Complete temporal knowledge graph with nodes and edges.
    """
    nodes: Dict[str, GraphNode] = Field(default_factory=dict, description="Nodes indexed by ID")
    edges: List[GraphEdge] = Field(default_factory=list, description="List of edges")
    
    # Graph metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Statistics
    total_nodes: int = Field(default=0)
    total_edges: int = Field(default=0)
    
    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.total_nodes = len(self.nodes)
        self.updated_at = datetime.now()
    
    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.total_edges = len(self.edges)
        self.updated_at = datetime.now()
        
        # Update node degrees
        if edge.source_id in self.nodes:
            self.nodes[edge.source_id].out_degree += 1
            self.nodes[edge.source_id].degree += 1
        if edge.target_id in self.nodes:
            self.nodes[edge.target_id].in_degree += 1
            self.nodes[edge.target_id].degree += 1
    
    def get_node_neighbors(self, node_id: str) -> List[str]:
        """Get all neighbor node IDs for a given node."""
        neighbors = set()
        for edge in self.edges:
            if edge.source_id == node_id:
                neighbors.add(edge.target_id)
            elif edge.target_id == node_id:
                neighbors.add(edge.source_id)
        return list(neighbors)
    
    def get_critical_nodes(self, threshold: float = 0.7) -> List[GraphNode]:
        """Get nodes with high risk scores."""
        return [
            node for node in self.nodes.values()
            if node.risk_score >= threshold
        ]
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.type == node_type]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class GraphFilter(BaseModel):
    """Filter parameters for graph queries."""
    node_types: Optional[List[NodeType]] = None
    edge_types: Optional[List[EdgeType]] = None
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    min_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_levels: Optional[List[RiskLevel]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    flagged_only: bool = False
    critical_only: bool = False


class InvestigationPath(BaseModel):
    """Represents a path of connected nodes for investigation."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_risk_score: float
    path_description: str
    key_insights: List[str] = Field(default_factory=list)
