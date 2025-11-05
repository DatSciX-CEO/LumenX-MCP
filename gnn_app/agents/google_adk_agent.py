"""
Google ADK (Agent Development Kit) integration for AI-powered analysis.
Provides intelligent agents for investigating nodes and suggesting actions.
"""

import os
from typing import Dict, List, Any, Optional
import structlog
from datetime import datetime
import json

try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    GenerativeModel = None

from gnn_app.config import settings
from gnn_app.core.graph_schema import GraphNode, GraphEdge, TemporalGraph

logger = structlog.get_logger()


class GoogleADKAgent:
    """
    AI Agent powered by Google's Gemini models.
    Provides intelligent analysis of graph nodes and investigative insights.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        api_key: Optional[str] = None
    ):
        """
        Initialize Google ADK agent.
        
        Args:
            model_name: Gemini model to use
            api_key: Google API key (or from settings/env)
        """
        if not GOOGLE_ADK_AVAILABLE:
            logger.warning("Google ADK not available - install google-generativeai")
            self.enabled = False
            return
        
        self.model_name = model_name
        self.api_key = api_key or settings.google_adk.api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            logger.warning("No Google API key found - ADK agent disabled")
            self.enabled = False
            return
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = GenerativeModel(model_name)
        self.enabled = True
        
        logger.info("Google ADK agent initialized", model=model_name)
    
    def analyze_node(
        self,
        node: GraphNode,
        neighbors: Optional[List[GraphNode]] = None,
        edges: Optional[List[GraphEdge]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a node and provide insights.
        
        Args:
            node: Node to analyze
            neighbors: Connected nodes
            edges: Edges connecting to this node
            
        Returns:
            Analysis results with insights and recommendations
        """
        if not self.enabled:
            return {"error": "Google ADK agent not enabled"}
        
        # Build context
        context = self._build_node_context(node, neighbors, edges)
        
        # Create prompt
        prompt = f"""You are Agent X, an AI assistant specialized in eDiscovery and risk analysis.
Analyze the following entity from a temporal knowledge graph and provide insights.

Entity Information:
{json.dumps(context, indent=2, default=str)}

Provide a comprehensive analysis including:
1. Risk Assessment: Evaluate the risk level and explain why
2. Key Connections: Highlight important relationships
3. Anomalies: Identify any unusual patterns
4. Recommendations: Suggest investigation actions
5. Timeline: Notable events or access patterns

Format your response as a structured analysis."""
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            analysis_text = response.text
            
            return {
                "success": True,
                "node_id": node.id,
                "analysis": analysis_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error analyzing node", error=str(e), node_id=node.id)
            return {
                "success": False,
                "error": str(e),
                "node_id": node.id
            }
    
    def suggest_investigation_path(
        self,
        start_node: GraphNode,
        graph: TemporalGraph,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Suggest an investigation path starting from a node.
        
        Args:
            start_node: Starting node
            graph: Complete temporal graph
            max_depth: Maximum path depth
            
        Returns:
            Suggested investigation path with reasoning
        """
        if not self.enabled:
            return {"error": "Google ADK agent not enabled"}
        
        # Get neighbors and high-risk connections
        neighbors = []
        high_risk_edges = []
        
        for edge in graph.edges:
            if edge.source_id == start_node.id:
                target = graph.nodes.get(edge.target_id)
                if target:
                    neighbors.append(target)
                    if edge.is_anomalous or target.risk_score > 0.6:
                        high_risk_edges.append(edge)
            elif edge.target_id == start_node.id:
                source = graph.nodes.get(edge.source_id)
                if source:
                    neighbors.append(source)
                    if edge.is_anomalous or source.risk_score > 0.6:
                        high_risk_edges.append(edge)
        
        # Build context
        context = {
            "start_node": {
                "id": start_node.id,
                "type": start_node.type.value,
                "label": start_node.label,
                "risk_score": start_node.risk_score,
                "risk_level": start_node.risk_level.value,
                "metadata": start_node.metadata
            },
            "neighbors": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "label": n.label,
                    "risk_score": n.risk_score
                }
                for n in neighbors[:10]  # Limit to top 10
            ],
            "high_risk_connections": [
                {
                    "edge_type": e.edge_type.value,
                    "source": e.source_id,
                    "target": e.target_id,
                    "is_anomalous": e.is_anomalous,
                    "timestamp": e.timestamp
                }
                for e in high_risk_edges[:5]
            ]
        }
        
        prompt = f"""You are Agent X, an expert in eDiscovery investigations.
Given the following starting point in a temporal knowledge graph, suggest the most effective investigation path.

Starting Point:
{json.dumps(context, indent=2, default=str)}

Provide:
1. Investigation Priority: Which nodes to investigate first and why
2. Path Strategy: Recommended sequence of nodes to examine
3. Key Questions: Critical questions to answer about each node
4. Red Flags: What patterns to watch for
5. Evidence Collection: What data to preserve

Format as a structured investigation plan."""
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            return {
                "success": True,
                "investigation_plan": response.text,
                "start_node_id": start_node.id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error suggesting investigation path", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def answer_query(
        self,
        query: str,
        node: Optional[GraphNode] = None,
        graph_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Answer a natural language query about a node or graph.
        
        Args:
            query: User's question
            node: Context node (optional)
            graph_context: Additional graph context (optional)
            
        Returns:
            Answer text
        """
        if not self.enabled:
            return "Google ADK agent is not enabled. Please configure API key."
        
        # Build context
        context_parts = []
        
        if node:
            context_parts.append(f"Selected Entity: {json.dumps({
                'id': node.id,
                'type': node.type.value,
                'label': node.label,
                'risk_score': node.risk_score,
                'relevance_score': node.relevance_score,
                'metadata': node.metadata
            }, indent=2, default=str)}")
        
        if graph_context:
            context_parts.append(f"Graph Context: {json.dumps(graph_context, indent=2, default=str)}")
        
        context = "\n\n".join(context_parts) if context_parts else "No specific context provided."
        
        prompt = f"""You are Agent X, an AI assistant for eDiscovery and risk management.
Answer the following question based on the provided context.

Context:
{context}

Question: {query}

Provide a clear, concise answer based on the data. If you cannot answer based on the available information, say so."""
        
        try:
            response = self.model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error("Error answering query", error=str(e))
            return f"Error processing query: {str(e)}"
    
    def _build_node_context(
        self,
        node: GraphNode,
        neighbors: Optional[List[GraphNode]] = None,
        edges: Optional[List[GraphEdge]] = None
    ) -> Dict[str, Any]:
        """Build context dictionary for a node."""
        context = {
            "id": node.id,
            "type": node.type.value,
            "label": node.label,
            "risk_score": node.risk_score,
            "risk_level": node.risk_level.value,
            "relevance_score": node.relevance_score,
            "metadata": node.metadata,
            "created_at": node.created_at,
            "degree": node.degree,
            "is_flagged": node.is_flagged,
            "is_critical": node.is_critical
        }
        
        if neighbors:
            context["neighbors"] = [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "label": n.label,
                    "risk_score": n.risk_score
                }
                for n in neighbors[:10]
            ]
        
        if edges:
            context["connections"] = [
                {
                    "type": e.edge_type.value,
                    "source": e.source_id,
                    "target": e.target_id,
                    "timestamp": e.timestamp,
                    "is_anomalous": e.is_anomalous
                }
                for e in edges[:10]
            ]
        
        return context


# Global agent instance
_adk_agent: Optional[GoogleADKAgent] = None


def get_adk_agent() -> GoogleADKAgent:
    """Get or create the global ADK agent instance."""
    global _adk_agent
    if _adk_agent is None:
        _adk_agent = GoogleADKAgent()
    return _adk_agent
