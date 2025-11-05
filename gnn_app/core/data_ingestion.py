"""
Data ingestion pipeline for building the temporal knowledge graph.
Supports multiple data sources: file systems, emails, collaboration platforms, etc.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
import json
import structlog
from abc import ABC, abstractmethod

from gnn_app.core.graph_schema import (
    GraphNode,
    GraphEdge,
    TemporalGraph,
    NodeType,
    EdgeType,
    RiskLevel
)

logger = structlog.get_logger()


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    @abstractmethod
    def ingest(self) -> tuple[List[GraphNode], List[GraphEdge]]:
        """
        Ingest data from source.
        
        Returns:
            Tuple of (nodes, edges)
        """
        pass


class FileSystemSource(DataSource):
    """
    Ingests data from file system metadata.
    Creates nodes for files and custodians, edges for access/edit/create.
    """
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
    
    def ingest(self) -> tuple[List[GraphNode], List[GraphEdge]]:
        """Ingest file system data from CSV."""
        logger.info("Ingesting file system data", path=self.data_path)
        
        nodes = []
        edges = []
        custodian_ids = set()
        
        try:
            df = pd.read_csv(self.data_path)
            
            for _, row in df.iterrows():
                # Create file node
                file_node = GraphNode(
                    id=f"file_{row.get('file_id', row.name)}",
                    type=NodeType.FILE,
                    label=row.get('file_name', 'Unknown File'),
                    metadata={
                        'file_type': row.get('file_type', ''),
                        'size': row.get('size_bytes', 0),
                        'path': row.get('file_path', ''),
                        'owner': row.get('owner', ''),
                        'sensitivity': row.get('sensitivity', 'normal'),
                    },
                    created_at=pd.to_datetime(row.get('created_at', datetime.now())),
                    last_accessed=pd.to_datetime(row.get('last_accessed', datetime.now()))
                )
                nodes.append(file_node)
                
                # Create custodian node if not exists
                owner_id = f"custodian_{row.get('owner', 'unknown')}"
                if owner_id not in custodian_ids:
                    custodian_node = GraphNode(
                        id=owner_id,
                        type=NodeType.CUSTODIAN,
                        label=row.get('owner', 'Unknown'),
                        metadata={
                            'role': row.get('owner_role', 'user'),
                            'department': row.get('department', 'unknown')
                        }
                    )
                    nodes.append(custodian_node)
                    custodian_ids.add(owner_id)
                
                # Create edges for file ownership and access
                edges.append(GraphEdge(
                    id=f"edge_created_{file_node.id}",
                    source_id=owner_id,
                    target_id=file_node.id,
                    edge_type=EdgeType.CREATED_FILE,
                    timestamp=file_node.created_at
                ))
                
                if file_node.last_accessed:
                    edges.append(GraphEdge(
                        id=f"edge_accessed_{file_node.id}",
                        source_id=owner_id,
                        target_id=file_node.id,
                        edge_type=EdgeType.ACCESSED_FILE,
                        timestamp=file_node.last_accessed
                    ))
            
            logger.info("File system data ingested", nodes=len(nodes), edges=len(edges))
            
        except Exception as e:
            logger.error("Error ingesting file system data", error=str(e))
        
        return nodes, edges


class EmailSource(DataSource):
    """
    Ingests email metadata.
    Creates nodes for emails and custodians, edges for sent/received.
    """
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
    
    def ingest(self) -> tuple[List[GraphNode], List[GraphEdge]]:
        """Ingest email data from CSV."""
        logger.info("Ingesting email data", path=self.data_path)
        
        nodes = []
        edges = []
        custodian_ids = set()
        
        try:
            df = pd.read_csv(self.data_path)
            
            for _, row in df.iterrows():
                # Create email node
                email_node = GraphNode(
                    id=f"email_{row.get('email_id', row.name)}",
                    type=NodeType.EMAIL,
                    label=row.get('subject', 'No Subject'),
                    metadata={
                        'sender': row.get('sender', ''),
                        'recipients': row.get('recipients', '').split(';'),
                        'has_attachments': row.get('has_attachments', False),
                        'importance': row.get('importance', 'normal')
                    },
                    created_at=pd.to_datetime(row.get('sent_at', datetime.now()))
                )
                nodes.append(email_node)
                
                # Create sender custodian
                sender_id = f"custodian_{row.get('sender', 'unknown')}"
                if sender_id not in custodian_ids:
                    custodian_node = GraphNode(
                        id=sender_id,
                        type=NodeType.CUSTODIAN,
                        label=row.get('sender', 'Unknown'),
                        metadata={'role': 'user'}
                    )
                    nodes.append(custodian_node)
                    custodian_ids.add(sender_id)
                
                # Create edge for sent email
                edges.append(GraphEdge(
                    id=f"edge_sent_{email_node.id}",
                    source_id=sender_id,
                    target_id=email_node.id,
                    edge_type=EdgeType.SENT_EMAIL,
                    timestamp=email_node.created_at
                ))
                
                # Create recipient custodians and edges
                recipients = row.get('recipients', '').split(';')
                for recipient in recipients:
                    if recipient:
                        recipient_id = f"custodian_{recipient.strip()}"
                        if recipient_id not in custodian_ids:
                            custodian_node = GraphNode(
                                id=recipient_id,
                                type=NodeType.CUSTODIAN,
                                label=recipient.strip(),
                                metadata={'role': 'user'}
                            )
                            nodes.append(custodian_node)
                            custodian_ids.add(recipient_id)
                        
                        edges.append(GraphEdge(
                            id=f"edge_received_{email_node.id}_{recipient_id}",
                            source_id=email_node.id,
                            target_id=recipient_id,
                            edge_type=EdgeType.RECEIVED_EMAIL,
                            timestamp=email_node.created_at
                        ))
            
            logger.info("Email data ingested", nodes=len(nodes), edges=len(edges))
            
        except Exception as e:
            logger.error("Error ingesting email data", error=str(e))
        
        return nodes, edges


class CollaborationSource(DataSource):
    """
    Ingests collaboration platform data (Slack, Teams).
    Creates nodes for channels and custodians, edges for membership.
    """
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
    
    def ingest(self) -> tuple[List[GraphNode], List[GraphEdge]]:
        """Ingest collaboration platform data from JSON."""
        logger.info("Ingesting collaboration data", path=self.data_path)
        
        nodes = []
        edges = []
        custodian_ids = set()
        
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            for channel_data in data.get('channels', []):
                # Create channel node
                channel_node = GraphNode(
                    id=f"channel_{channel_data['id']}",
                    type=NodeType.CHANNEL,
                    label=channel_data.get('name', 'Unknown Channel'),
                    metadata={
                        'platform': channel_data.get('platform', 'slack'),
                        'is_private': channel_data.get('is_private', False),
                        'member_count': len(channel_data.get('members', [])),
                        'topic': channel_data.get('topic', '')
                    },
                    created_at=pd.to_datetime(channel_data.get('created_at', datetime.now()))
                )
                nodes.append(channel_node)
                
                # Create members and edges
                for member in channel_data.get('members', []):
                    member_id = f"custodian_{member['email']}"
                    if member_id not in custodian_ids:
                        custodian_node = GraphNode(
                            id=member_id,
                            type=NodeType.CUSTODIAN,
                            label=member.get('name', member['email']),
                            metadata={
                                'role': member.get('role', 'user'),
                                'department': member.get('department', 'unknown')
                            }
                        )
                        nodes.append(custodian_node)
                        custodian_ids.add(member_id)
                    
                    edges.append(GraphEdge(
                        id=f"edge_member_{channel_node.id}_{member_id}",
                        source_id=member_id,
                        target_id=channel_node.id,
                        edge_type=EdgeType.MEMBER_OF_CHANNEL,
                        timestamp=channel_node.created_at
                    ))
            
            logger.info("Collaboration data ingested", nodes=len(nodes), edges=len(edges))
            
        except Exception as e:
            logger.error("Error ingesting collaboration data", error=str(e))
        
        return nodes, edges


class DataIngestionPipeline:
    """
    Main data ingestion pipeline.
    Orchestrates ingestion from multiple sources and builds the temporal graph.
    """
    
    def __init__(self):
        self.sources: List[DataSource] = []
        self.graph = TemporalGraph()
    
    def add_source(self, source: DataSource):
        """Add a data source to the pipeline."""
        self.sources.append(source)
    
    def ingest_all(self) -> TemporalGraph:
        """
        Ingest data from all sources and build the temporal graph.
        
        Returns:
            Complete temporal graph
        """
        logger.info("Starting data ingestion", num_sources=len(self.sources))
        
        all_nodes = []
        all_edges = []
        
        for source in self.sources:
            nodes, edges = source.ingest()
            all_nodes.extend(nodes)
            all_edges.extend(edges)
        
        # Build graph
        node_id_map = {}
        for node in all_nodes:
            if node.id not in node_id_map:
                self.graph.add_node(node)
                node_id_map[node.id] = node
            else:
                # Merge duplicate nodes
                existing = node_id_map[node.id]
                existing.metadata.update(node.metadata)
        
        for edge in all_edges:
            self.graph.add_edge(edge)
        
        # Update time range
        if self.graph.edges:
            timestamps = [e.timestamp for e in self.graph.edges]
            self.graph.start_date = min(timestamps)
            self.graph.end_date = max(timestamps)
        
        logger.info(
            "Data ingestion complete",
            nodes=self.graph.total_nodes,
            edges=self.graph.total_edges,
            start_date=self.graph.start_date,
            end_date=self.graph.end_date
        )
        
        return self.graph
    
    def create_mock_graph(self) -> TemporalGraph:
        """Create a mock graph for testing and demonstration."""
        logger.info("Creating mock graph")
        
        # Create custodians
        custodians = [
            GraphNode(
                id="custodian_john_doe",
                type=NodeType.CUSTODIAN,
                label="John Doe",
                metadata={"role": "engineer", "department": "R&D"},
                relevance_score=0.8,
                risk_level=RiskLevel.MEDIUM,
                risk_score=0.6
            ),
            GraphNode(
                id="custodian_jane_smith",
                type=NodeType.CUSTODIAN,
                label="Jane Smith",
                metadata={"role": "manager", "department": "Legal"},
                relevance_score=0.9,
                risk_level=RiskLevel.HIGH,
                risk_score=0.75
            ),
            GraphNode(
                id="custodian_bob_wilson",
                type=NodeType.CUSTODIAN,
                label="Bob Wilson",
                metadata={"role": "sales", "department": "Sales"},
                relevance_score=0.5,
                risk_level=RiskLevel.LOW,
                risk_score=0.3
            ),
        ]
        
        # Create files
        files = [
            GraphNode(
                id="file_contract_001",
                type=NodeType.FILE,
                label="Contract_2024_001.pdf",
                metadata={
                    "file_type": "pdf",
                    "sensitivity": "high",
                    "owner": "jane_smith"
                },
                relevance_score=0.95,
                risk_level=RiskLevel.HIGH,
                risk_score=0.8,
                is_critical=True
            ),
            GraphNode(
                id="file_source_code",
                type=NodeType.FILE,
                label="proprietary_algorithm.py",
                metadata={
                    "file_type": "code",
                    "sensitivity": "critical",
                    "owner": "john_doe"
                },
                relevance_score=0.98,
                risk_level=RiskLevel.CRITICAL,
                risk_score=0.95,
                is_critical=True
            ),
        ]
        
        # Create channels
        channels = [
            GraphNode(
                id="channel_legal_team",
                type=NodeType.CHANNEL,
                label="#legal-team",
                metadata={"platform": "slack", "is_private": True, "member_count": 5},
                relevance_score=0.7,
                risk_level=RiskLevel.MEDIUM,
                risk_score=0.5
            ),
        ]
        
        # Add all nodes
        for node in custodians + files + channels:
            self.graph.add_node(node)
        
        # Create edges
        edges = [
            GraphEdge(
                id="edge_1",
                source_id="custodian_jane_smith",
                target_id="file_contract_001",
                edge_type=EdgeType.CREATED_FILE,
                timestamp=datetime.now() - timedelta(days=10)
            ),
            GraphEdge(
                id="edge_2",
                source_id="custodian_john_doe",
                target_id="file_source_code",
                edge_type=EdgeType.CREATED_FILE,
                timestamp=datetime.now() - timedelta(days=30)
            ),
            GraphEdge(
                id="edge_3",
                source_id="custodian_bob_wilson",
                target_id="file_source_code",
                edge_type=EdgeType.ACCESSED_FILE,
                timestamp=datetime.now() - timedelta(days=2),
                is_anomalous=True,
                risk_contribution=0.8
            ),
            GraphEdge(
                id="edge_4",
                source_id="custodian_jane_smith",
                target_id="channel_legal_team",
                edge_type=EdgeType.MEMBER_OF_CHANNEL,
                timestamp=datetime.now() - timedelta(days=90)
            ),
        ]
        
        for edge in edges:
            self.graph.add_edge(edge)
        
        logger.info("Mock graph created", nodes=self.graph.total_nodes, edges=self.graph.total_edges)
        
        return self.graph
