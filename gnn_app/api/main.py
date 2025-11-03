"""
FastAPI backend for the GNN application.
Provides REST API endpoints for graph operations, predictions, and AI agents.
"""

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import structlog
import asyncio

from gnn_app.config import settings
from gnn_app.core.graph_schema import (
    TemporalGraph,
    GraphNode,
    GraphEdge,
    GraphFilter,
    NodeType,
    RiskLevel
)
from gnn_app.core.data_ingestion import DataIngestionPipeline
from gnn_app.services.gnn_processor import get_gnn_processor
from gnn_app.agents.google_adk_agent import get_adk_agent
from gnn_app.services.llm_service import get_ollama_service

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="GNN-powered predictive data mapping for eDiscovery and risk management"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
graph: Optional[TemporalGraph] = None
gnn_processor = None


# Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    node_id: Optional[str] = None
    use_ollama: bool = False


class ChatResponse(BaseModel):
    response: str
    timestamp: str


class AnalysisRequest(BaseModel):
    node_id: str


class ForecastRequest(BaseModel):
    node_id: str
    months_ahead: int = 3


class InvestigationPathRequest(BaseModel):
    start_node_id: str
    max_depth: int = 3
    min_risk: float = 0.5


# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global graph, gnn_processor
    
    logger.info("Starting GNN application", version=settings.version)
    
    # Initialize GNN processor
    gnn_processor = get_gnn_processor()
    
    # Load or create graph
    pipeline = DataIngestionPipeline()
    graph = pipeline.create_mock_graph()
    
    # Process graph through GNN
    graph = gnn_processor.process_graph(graph)
    
    # Check Ollama availability
    ollama = get_ollama_service()
    await ollama.check_availability()
    
    logger.info("GNN application started", nodes=graph.total_nodes, edges=graph.total_edges)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down GNN application")
    ollama = get_ollama_service()
    await ollama.close()


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "timestamp": datetime.now().isoformat()
    }


# Graph endpoints
@app.get("/api/graph")
async def get_graph(
    node_types: Optional[List[NodeType]] = Query(None),
    min_relevance: float = Query(0.0, ge=0.0, le=1.0),
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    risk_levels: Optional[List[RiskLevel]] = Query(None),
    flagged_only: bool = False,
    critical_only: bool = False
):
    """
    Get the temporal graph with optional filters.
    """
    if not graph:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    # Apply filters
    filtered_nodes = []
    for node in graph.nodes.values():
        # Type filter
        if node_types and node.type not in node_types:
            continue
        
        # Score filters
        if node.relevance_score < min_relevance:
            continue
        if node.risk_score < min_risk:
            continue
        
        # Risk level filter
        if risk_levels and node.risk_level not in risk_levels:
            continue
        
        # Flag filters
        if flagged_only and not node.is_flagged:
            continue
        if critical_only and not node.is_critical:
            continue
        
        filtered_nodes.append(node)
    
    # Filter edges to only include those between filtered nodes
    filtered_node_ids = {n.id for n in filtered_nodes}
    filtered_edges = [
        e for e in graph.edges
        if e.source_id in filtered_node_ids and e.target_id in filtered_node_ids
    ]
    
    return {
        "nodes": [n.model_dump() for n in filtered_nodes],
        "edges": [e.model_dump() for e in filtered_edges],
        "metadata": {
            "total_nodes": len(filtered_nodes),
            "total_edges": len(filtered_edges),
            "start_date": graph.start_date,
            "end_date": graph.end_date
        }
    }


@app.get("/api/nodes/{node_id}")
async def get_node(node_id: str):
    """Get details for a specific node."""
    if not graph or node_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node = graph.nodes[node_id]
    neighbors = graph.get_node_neighbors(node_id)
    neighbor_nodes = [graph.nodes[nid] for nid in neighbors if nid in graph.nodes]
    
    # Get connected edges
    connected_edges = [
        e for e in graph.edges
        if e.source_id == node_id or e.target_id == node_id
    ]
    
    return {
        "node": node.model_dump(),
        "neighbors": [n.model_dump() for n in neighbor_nodes[:10]],
        "edges": [e.model_dump() for e in connected_edges[:20]],
        "metrics": {
            "neighbor_count": len(neighbors),
            "edge_count": len(connected_edges),
            "avg_neighbor_risk": sum(n.risk_score for n in neighbor_nodes) / len(neighbor_nodes) if neighbor_nodes else 0
        }
    }


@app.get("/api/critical-files")
async def get_critical_files(top_k: int = Query(10, ge=1, le=100)):
    """Get the most critical files."""
    if not graph or not gnn_processor:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    critical_files = gnn_processor.get_critical_files(graph, top_k)
    
    return {
        "files": [f.model_dump() for f in critical_files],
        "count": len(critical_files)
    }


@app.post("/api/investigation-path")
async def get_investigation_path(request: InvestigationPathRequest):
    """Get investigation path from a starting node."""
    if not graph or not gnn_processor:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    path = gnn_processor.find_investigation_path(
        graph,
        request.start_node_id,
        request.max_depth,
        request.min_risk
    )
    
    return {
        "path": [n.model_dump() for n in path],
        "length": len(path),
        "start_node_id": request.start_node_id
    }


@app.post("/api/forecast")
async def forecast_risk(request: ForecastRequest):
    """Forecast future risk for a node."""
    if not graph or not gnn_processor:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if request.node_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    
    forecasted_risk = gnn_processor.forecast_temporal_risk(
        graph,
        request.node_id,
        request.months_ahead
    )
    
    # Update node
    graph.nodes[request.node_id].forecasted_risk = forecasted_risk
    
    return {
        "node_id": request.node_id,
        "current_risk": graph.nodes[request.node_id].risk_score,
        "forecasted_risk": forecasted_risk,
        "months_ahead": request.months_ahead,
        "change": forecasted_risk - graph.nodes[request.node_id].risk_score
    }


# AI Agent endpoints
@app.post("/api/analyze", response_model=Dict[str, Any])
async def analyze_node(request: AnalysisRequest):
    """Analyze a node using AI agent."""
    if not graph:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    if request.node_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node = graph.nodes[request.node_id]
    neighbors = [graph.nodes[nid] for nid in graph.get_node_neighbors(request.node_id) if nid in graph.nodes]
    edges = [e for e in graph.edges if e.source_id == request.node_id or e.target_id == request.node_id]
    
    # Try Google ADK first
    adk_agent = get_adk_agent()
    if adk_agent.enabled:
        result = adk_agent.analyze_node(node, neighbors, edges)
        return result
    
    # Fallback to Ollama
    ollama = get_ollama_service()
    analysis = await ollama.analyze_node(node, neighbors)
    
    return {
        "success": True,
        "node_id": node.id,
        "analysis": analysis,
        "timestamp": datetime.now().isoformat(),
        "provider": "ollama"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with AI assistant about a node or general query."""
    node = None
    if request.node_id and graph and request.node_id in graph.nodes:
        node = graph.nodes[request.node_id]
    
    # Choose provider
    if request.use_ollama:
        ollama = get_ollama_service()
        response = await ollama.answer_query(request.message, node)
        provider = "ollama"
    else:
        adk_agent = get_adk_agent()
        if adk_agent.enabled:
            response = adk_agent.answer_query(request.message, node)
            provider = "google_adk"
        else:
            ollama = get_ollama_service()
            response = await ollama.answer_query(request.message, node)
            provider = "ollama"
    
    return ChatResponse(
        response=response,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/stats")
async def get_stats():
    """Get graph statistics."""
    if not graph:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    # Compute statistics
    risk_distribution = {
        "low": sum(1 for n in graph.nodes.values() if n.risk_level == RiskLevel.LOW),
        "medium": sum(1 for n in graph.nodes.values() if n.risk_level == RiskLevel.MEDIUM),
        "high": sum(1 for n in graph.nodes.values() if n.risk_level == RiskLevel.HIGH),
        "critical": sum(1 for n in graph.nodes.values() if n.risk_level == RiskLevel.CRITICAL),
    }
    
    node_types = {}
    for node in graph.nodes.values():
        node_types[node.type.value] = node_types.get(node.type.value, 0) + 1
    
    avg_risk = sum(n.risk_score for n in graph.nodes.values()) / len(graph.nodes) if graph.nodes else 0
    avg_relevance = sum(n.relevance_score for n in graph.nodes.values()) / len(graph.nodes) if graph.nodes else 0
    
    return {
        "total_nodes": graph.total_nodes,
        "total_edges": graph.total_edges,
        "risk_distribution": risk_distribution,
        "node_types": node_types,
        "avg_risk_score": avg_risk,
        "avg_relevance_score": avg_relevance,
        "critical_nodes": sum(1 for n in graph.nodes.values() if n.is_critical),
        "flagged_nodes": sum(1 for n in graph.nodes.values() if n.is_flagged),
        "date_range": {
            "start": graph.start_date,
            "end": graph.end_date
        }
    }


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload
    )
